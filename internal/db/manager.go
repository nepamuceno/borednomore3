package db

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	_ "github.com/lib/pq"
	_ "modernc.org/sqlite"
)

type DBMode string

const (
	ModeSQLite   DBMode = "sqlite"
	ModePostgres DBMode = "postgres"
)

type Manager struct {
	adminDB *sql.DB
	dbsPath string
	mode    DBMode
	pgDSN   string
	mu      sync.RWMutex
	pool    map[int64]*sql.DB
}

var instance *Manager
var once sync.Once

func Get() *Manager { return instance }

func Init(dbsPath string) error {
	var err error
	once.Do(func() {
		mode := DBMode(envOr("DB_MODE", "sqlite"))
		m := &Manager{dbsPath: dbsPath, mode: mode, pool: make(map[int64]*sql.DB)}
		if mode == ModePostgres {
			m.pgDSN = envOr("DB_DSN_BASE", "postgres://desar:desar@localhost/")
			err = m.initAdminPG()
		} else {
			if e := os.MkdirAll(dbsPath, 0750); e != nil { err = e; return }
			err = m.initAdminSQLite()
		}
		if err == nil { instance = m }
	})
	return err
}

func (m *Manager) Mode() DBMode     { return m.mode }
func (m *Manager) AdminDB() *sql.DB { return m.adminDB }

func (m *Manager) initAdminSQLite() error {
	path := filepath.Join(m.dbsPath, "admin.db")
	db, err := sql.Open("sqlite", path)
	if err != nil { return fmt.Errorf("admin sqlite: %w", err) }
	db.SetMaxOpenConns(1)
	m.adminDB = db
	return m.migrateAdmin()
}

func (m *Manager) initAdminPG() error {
	dsn := envOr("DB_ADMIN_DSN", m.pgDSN+"desar_admin")
	db, err := sql.Open("postgres", dsn)
	if err != nil { return fmt.Errorf("admin postgres: %w", err) }
	db.SetMaxOpenConns(20)
	m.adminDB = db
	return m.migrateAdmin()
}

func (m *Manager) migrateAdmin() error {
	for _, s := range m.adminDDL() {
		s = strings.TrimSpace(s)
		if s == "" { continue }
		if _, err := m.adminDB.Exec(s); err != nil {
			return fmt.Errorf("migrate admin: %v — %.60s", err, s)
		}
	}
	return nil
}

func (m *Manager) adminDDL() []string {
	if m.mode == ModePostgres {
		return []string{
			`CREATE TABLE IF NOT EXISTS companias (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				nombre TEXT NOT NULL, rfc TEXT, email TEXT, telefono TEXT,
				direccion TEXT, ciudad TEXT, estado TEXT, pais TEXT DEFAULT 'Mexico',
				logo TEXT, api_key TEXT NOT NULL UNIQUE, plan TEXT NOT NULL DEFAULT 'basico',
				max_empleados INTEGER DEFAULT 25, max_dispositivos INTEGER DEFAULT 3,
				activo INTEGER DEFAULT 1, fecha_vence TEXT,
				fecha_creado TEXT NOT NULL DEFAULT to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS'),
				db_path TEXT NOT NULL DEFAULT '')`,
			`CREATE TABLE IF NOT EXISTS usuarios (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				compania_id INTEGER NOT NULL REFERENCES companias(id),
				nombre TEXT NOT NULL, email TEXT NOT NULL, password_hash TEXT NOT NULL,
				rol TEXT NOT NULL DEFAULT 'readonly', sitio_id INTEGER DEFAULT 0,
				activo INTEGER DEFAULT 1, ultimo_login TEXT,
				fecha_creado TEXT NOT NULL DEFAULT to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS'),
				UNIQUE(compania_id, email))`,
			`CREATE TABLE IF NOT EXISTS sesiones (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				usuario_id INTEGER NOT NULL, token TEXT NOT NULL UNIQUE,
				ip TEXT, user_agent TEXT,
				creado TEXT NOT NULL DEFAULT to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS'),
				expira TEXT NOT NULL, activo INTEGER DEFAULT 1)`,
			`CREATE TABLE IF NOT EXISTS auditoria (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				compania_id INTEGER, usuario_id INTEGER, accion TEXT NOT NULL,
				tabla TEXT, registro_id INTEGER, detalle TEXT, ip TEXT,
				ts TEXT NOT NULL DEFAULT to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS'))`,
			`CREATE TABLE IF NOT EXISTS dispositivos (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				compania_id INTEGER NOT NULL REFERENCES companias(id),
				nombre TEXT, api_key TEXT NOT NULL, ultimo_sync TEXT,
				activo INTEGER DEFAULT 1,
				fecha_reg TEXT NOT NULL DEFAULT to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS'))`,
			`CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)`,
			`CREATE INDEX IF NOT EXISTS idx_auditoria_cia ON auditoria(compania_id)`,
		}
	}
	return []string{`
	PRAGMA journal_mode=WAL;
	CREATE TABLE IF NOT EXISTS companias (
		id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, rfc TEXT, email TEXT,
		telefono TEXT, direccion TEXT, ciudad TEXT, estado TEXT, pais TEXT DEFAULT 'Mexico',
		logo TEXT, api_key TEXT NOT NULL UNIQUE, plan TEXT NOT NULL DEFAULT 'basico',
		max_empleados INTEGER DEFAULT 25, max_dispositivos INTEGER DEFAULT 3,
		activo INTEGER DEFAULT 1, fecha_vence TEXT,
		fecha_creado TEXT NOT NULL DEFAULT (datetime('now')), db_path TEXT NOT NULL);
	CREATE TABLE IF NOT EXISTS usuarios (
		id INTEGER PRIMARY KEY AUTOINCREMENT, compania_id INTEGER NOT NULL,
		nombre TEXT NOT NULL, email TEXT NOT NULL, password_hash TEXT NOT NULL,
		rol TEXT NOT NULL DEFAULT 'readonly', sitio_id INTEGER DEFAULT 0,
		activo INTEGER DEFAULT 1, ultimo_login TEXT,
		fecha_creado TEXT NOT NULL DEFAULT (datetime('now')),
		FOREIGN KEY (compania_id) REFERENCES companias(id), UNIQUE(compania_id, email));
	CREATE TABLE IF NOT EXISTS sesiones (
		id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
		token TEXT NOT NULL UNIQUE, ip TEXT, user_agent TEXT,
		creado TEXT NOT NULL DEFAULT (datetime('now')), expira TEXT NOT NULL, activo INTEGER DEFAULT 1);
	CREATE TABLE IF NOT EXISTS auditoria (
		id INTEGER PRIMARY KEY AUTOINCREMENT, compania_id INTEGER, usuario_id INTEGER,
		accion TEXT NOT NULL, tabla TEXT, registro_id INTEGER, detalle TEXT, ip TEXT,
		ts TEXT NOT NULL DEFAULT (datetime('now')));
	CREATE TABLE IF NOT EXISTS dispositivos (
		id INTEGER PRIMARY KEY AUTOINCREMENT, compania_id INTEGER NOT NULL,
		nombre TEXT, api_key TEXT NOT NULL, ultimo_sync TEXT, activo INTEGER DEFAULT 1,
		fecha_reg TEXT NOT NULL DEFAULT (datetime('now')),
		FOREIGN KEY (compania_id) REFERENCES companias(id));
	CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
	CREATE INDEX IF NOT EXISTS idx_auditoria_cia ON auditoria(compania_id);`}
}

func (m *Manager) CompanyDB(companyID int64) (*sql.DB, error) {
	m.mu.RLock()
	db, ok := m.pool[companyID]
	m.mu.RUnlock()
	if ok { return db, nil }
	var dbPath string
	err := m.adminDB.QueryRow(Q("SELECT db_path FROM companias WHERE id=$1"), companyID).Scan(&dbPath)
	if err != nil { return nil, fmt.Errorf("compania %d no encontrada: %w", companyID, err) }
	return m.openCompanyDB(companyID, dbPath)
}

func (m *Manager) openCompanyDB(companyID int64, path string) (*sql.DB, error) {
	var db *sql.DB
	var err error
	if m.mode == ModePostgres {
		db, err = sql.Open("postgres", m.pgDSN+path)
		if err != nil { return nil, err }
		db.SetMaxOpenConns(10)
	} else {
		if err = os.MkdirAll(filepath.Dir(path), 0750); err != nil { return nil, err }
		db, err = sql.Open("sqlite", path)
		if err != nil { return nil, err }
		db.SetMaxOpenConns(1)
	}
	if err = migrateCompany(db, m.mode); err != nil { return nil, err }
	m.mu.Lock()
	m.pool[companyID] = db
	m.mu.Unlock()
	return db, nil
}

func migrateCompany(db *sql.DB, mode DBMode) error {
	for _, s := range companyDDL(mode) {
		s = strings.TrimSpace(s)
		if s == "" { continue }
		if _, err := db.Exec(s); err != nil {
			return fmt.Errorf("migrate company: %v — %.60s", err, s)
		}
	}
	return nil
}

func companyDDL(mode DBMode) []string {
	if mode == ModePostgres {
		return []string{
			`CREATE TABLE IF NOT EXISTS empleados (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				codigo_empleado TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL,
				direccion TEXT, ciudad TEXT, estado TEXT, pais TEXT, codigo_postal TEXT,
				telefono TEXT, telefono_emergencia TEXT, fecha_nacimiento TEXT,
				rfc TEXT, seguro_social TEXT, numero_identificacion TEXT, puesto TEXT,
				tipo_sangre TEXT, notas TEXT, foto_perfil TEXT,
				foto_rostro_1 TEXT, foto_rostro_2 TEXT, foto_rostro_3 TEXT,
				embedding_1 TEXT, embedding_2 TEXT, embedding_3 TEXT,
				sitio_trabajo TEXT, activo INTEGER NOT NULL DEFAULT 1,
				fecha_registro TEXT DEFAULT to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS'),
				fecha_alta TEXT, fecha_vencimiento TEXT, sync_status INTEGER NOT NULL DEFAULT 0)`,
			`CREATE TABLE IF NOT EXISTS registros (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				empleado_id INTEGER NOT NULL REFERENCES empleados(id),
				codigo_empleado TEXT NOT NULL, nombre_empleado TEXT NOT NULL,
				tipo TEXT NOT NULL, timestamp TEXT NOT NULL,
				gps_lat REAL DEFAULT 0, gps_lon REAL DEFAULT 0,
				sitio_trabajo TEXT, metodo TEXT DEFAULT 'manual',
				notas TEXT, sync_status INTEGER NOT NULL DEFAULT 1)`,
			`CREATE TABLE IF NOT EXISTS sitios (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				nombre TEXT NOT NULL UNIQUE, descripcion TEXT,
				gps_lat REAL DEFAULT 0, gps_lon REAL DEFAULT 0,
				geofence_radio_metros REAL DEFAULT 100, geofence_tipo TEXT DEFAULT 'permitido',
				geofence_activo INTEGER DEFAULT 0, tipo_sitio TEXT DEFAULT 'normal',
				recibir_advertencias INTEGER DEFAULT 0, activo INTEGER DEFAULT 1)`,
			`CREATE TABLE IF NOT EXISTS configuracion (
				id INTEGER PRIMARY KEY DEFAULT 1,
				nombre_compania TEXT NOT NULL DEFAULT 'Mi Compañía', rfc_compania TEXT,
				direccion_compania TEXT, ciudad_compania TEXT, estado_compania TEXT,
				pais_compania TEXT, codigo_postal_compania TEXT, telefono_compania TEXT,
				email_compania TEXT, logo_compania TEXT,
				zona_horaria TEXT DEFAULT 'America/Mexico_City',
				whatsapp_api_url TEXT, whatsapp_api_token TEXT, whatsapp_channel_id TEXT,
				whatsapp_phone_number_id TEXT, whatsapp_verify_token TEXT,
				whatsapp_habilitado INTEGER DEFAULT 0, telegram_bot_token TEXT,
				telegram_chat_id TEXT, telegram_habilitado INTEGER DEFAULT 0,
				bot_prefijo TEXT DEFAULT '/', hora_entrada_default TEXT DEFAULT '08:00',
				hora_salida_default TEXT DEFAULT '17:00', tolerancia_minutos INTEGER DEFAULT 15,
				jornada_horas REAL DEFAULT 8.0, umbral_reconocimiento REAL DEFAULT 0.80,
				pedir_confirmacion_nuevo INTEGER DEFAULT 1, formato_reporte_default TEXT DEFAULT 'excel')`,
			`CREATE TABLE IF NOT EXISTS jornadas (
				id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
				empleado_id INTEGER NOT NULL REFERENCES empleados(id),
				codigo_empleado TEXT NOT NULL, nombre_empleado TEXT NOT NULL,
				fecha TEXT NOT NULL, entrada_timestamp TEXT, salida_timestamp TEXT,
				horas_trabajadas REAL, completa INTEGER NOT NULL DEFAULT 0, sitio_trabajo TEXT)`,
			`CREATE INDEX IF NOT EXISTS idx_registros_ts ON registros(timestamp)`,
			`CREATE INDEX IF NOT EXISTS idx_registros_emp ON registros(codigo_empleado)`,
			`CREATE INDEX IF NOT EXISTS idx_empleados_cod ON empleados(codigo_empleado)`,
			`CREATE INDEX IF NOT EXISTS idx_jornadas_emp ON jornadas(empleado_id, fecha)`,
		}
	}
	return []string{`
	PRAGMA journal_mode=WAL;
	CREATE TABLE IF NOT EXISTS empleados (
		id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_empleado TEXT NOT NULL UNIQUE,
		nombre TEXT NOT NULL, direccion TEXT, ciudad TEXT, estado TEXT, pais TEXT,
		codigo_postal TEXT, telefono TEXT, telefono_emergencia TEXT, fecha_nacimiento TEXT,
		rfc TEXT, seguro_social TEXT, numero_identificacion TEXT, puesto TEXT,
		tipo_sangre TEXT, notas TEXT, foto_perfil TEXT,
		foto_rostro_1 TEXT, foto_rostro_2 TEXT, foto_rostro_3 TEXT,
		embedding_1 TEXT, embedding_2 TEXT, embedding_3 TEXT,
		sitio_trabajo TEXT, activo INTEGER NOT NULL DEFAULT 1,
		fecha_registro TEXT DEFAULT (datetime('now')), fecha_alta TEXT,
		fecha_vencimiento TEXT, sync_status INTEGER NOT NULL DEFAULT 0);
	CREATE TABLE IF NOT EXISTS registros (
		id INTEGER PRIMARY KEY AUTOINCREMENT, empleado_id INTEGER NOT NULL,
		codigo_empleado TEXT NOT NULL, nombre_empleado TEXT NOT NULL,
		tipo TEXT NOT NULL, timestamp TEXT NOT NULL,
		gps_lat REAL DEFAULT 0, gps_lon REAL DEFAULT 0,
		sitio_trabajo TEXT, metodo TEXT DEFAULT 'manual', notas TEXT,
		sync_status INTEGER NOT NULL DEFAULT 1,
		FOREIGN KEY (empleado_id) REFERENCES empleados(id));
	CREATE TABLE IF NOT EXISTS sitios (
		id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
		descripcion TEXT, gps_lat REAL DEFAULT 0, gps_lon REAL DEFAULT 0,
		geofence_radio_metros REAL DEFAULT 100, geofence_tipo TEXT DEFAULT 'permitido',
		geofence_activo INTEGER DEFAULT 0, tipo_sitio TEXT DEFAULT 'normal',
		recibir_advertencias INTEGER DEFAULT 0, activo INTEGER DEFAULT 1);
	CREATE TABLE IF NOT EXISTS configuracion (
		id INTEGER PRIMARY KEY DEFAULT 1,
		nombre_compania TEXT NOT NULL DEFAULT 'Mi Compañía', rfc_compania TEXT,
		direccion_compania TEXT, ciudad_compania TEXT, estado_compania TEXT,
		pais_compania TEXT, codigo_postal_compania TEXT, telefono_compania TEXT,
		email_compania TEXT, logo_compania TEXT,
		zona_horaria TEXT DEFAULT 'America/Mexico_City',
		whatsapp_api_url TEXT, whatsapp_api_token TEXT, whatsapp_channel_id TEXT,
		whatsapp_phone_number_id TEXT, whatsapp_verify_token TEXT,
		whatsapp_habilitado INTEGER DEFAULT 0, telegram_bot_token TEXT,
		telegram_chat_id TEXT, telegram_habilitado INTEGER DEFAULT 0,
		bot_prefijo TEXT DEFAULT '/', hora_entrada_default TEXT DEFAULT '08:00',
		hora_salida_default TEXT DEFAULT '17:00', tolerancia_minutos INTEGER DEFAULT 15,
		jornada_horas REAL DEFAULT 8.0, umbral_reconocimiento REAL DEFAULT 0.80,
		pedir_confirmacion_nuevo INTEGER DEFAULT 1, formato_reporte_default TEXT DEFAULT 'excel');
	CREATE TABLE IF NOT EXISTS jornadas (
		id INTEGER PRIMARY KEY AUTOINCREMENT, empleado_id INTEGER NOT NULL,
		codigo_empleado TEXT NOT NULL, nombre_empleado TEXT NOT NULL,
		fecha TEXT NOT NULL, entrada_timestamp TEXT, salida_timestamp TEXT,
		horas_trabajadas REAL, completa INTEGER NOT NULL DEFAULT 0, sitio_trabajo TEXT,
		FOREIGN KEY (empleado_id) REFERENCES empleados(id));
	CREATE INDEX IF NOT EXISTS idx_registros_ts ON registros(timestamp);
	CREATE INDEX IF NOT EXISTS idx_registros_emp ON registros(codigo_empleado);
	CREATE INDEX IF NOT EXISTS idx_empleados_cod ON empleados(codigo_empleado);
	CREATE INDEX IF NOT EXISTS idx_jornadas_emp ON jornadas(empleado_id, fecha);`}
}

func (m *Manager) CompanyDBByKey(apiKey string) (*sql.DB, int64, error) {
	var id int64
	var dbPath string
	var activo int
	err := m.adminDB.QueryRow(
		Q("SELECT id, db_path, activo FROM companias WHERE api_key=$1"), apiKey,
	).Scan(&id, &dbPath, &activo)
	if err != nil { return nil, 0, fmt.Errorf("api_key no válido") }
	if activo == 0 { return nil, 0, fmt.Errorf("compañía inactiva") }
	db, err := m.openCompanyDB(id, dbPath)
	return db, id, err
}

func (m *Manager) Audit(companyID, userID int64, accion, tabla string, regID int64, detalle, ip string) {
	m.adminDB.Exec(
		Q(`INSERT INTO auditoria(compania_id,usuario_id,accion,tabla,registro_id,detalle,ip) VALUES($1,$2,$3,$4,$5,$6,$7)`),
		companyID, userID, accion, tabla, regID, detalle, ip,
	)
}

func (m *Manager) NewCompanyDBPath(apiKey string) string {
	suffix := apiKey[6:14]
	if m.mode == ModePostgres {
		return "desar_company_" + suffix
	}
	return "./data/company_" + suffix + ".db"
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" { return v }
	return def
}
