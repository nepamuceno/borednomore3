package db

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	_ "modernc.org/sqlite"
)

// Manager gestiona la BD admin y una BD SQLite por compañía
type Manager struct {
	adminDB  *sql.DB
	dbsPath  string
	mu       sync.RWMutex
	pool     map[int64]*sql.DB
}

var instance *Manager
var once    sync.Once

func Get() *Manager {
	return instance
}

func Init(dbsPath string) error {
	var err error
	once.Do(func() {
		if e := os.MkdirAll(dbsPath, 0750); e != nil {
			err = e
			return
		}
		m := &Manager{dbsPath: dbsPath, pool: make(map[int64]*sql.DB)}
		if e := m.initAdmin(); e != nil {
			err = e
			return
		}
		instance = m
	})
	return err
}

// ── BD Admin ──────────────────────────────────────────────────
func (m *Manager) initAdmin() error {
	path := filepath.Join(m.dbsPath, "admin.db")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return fmt.Errorf("admin db: %w", err)
	}
	db.SetMaxOpenConns(1) // SQLite: una conexión de escritura
	m.adminDB = db
	return m.migrateAdmin()
}

func (m *Manager) AdminDB() *sql.DB { return m.adminDB }

func (m *Manager) migrateAdmin() error {
	_, err := m.adminDB.Exec(`
	PRAGMA journal_mode=WAL;

	CREATE TABLE IF NOT EXISTS companias (
		id               INTEGER PRIMARY KEY AUTOINCREMENT,
		nombre           TEXT NOT NULL,
		rfc              TEXT,
		email            TEXT,
		telefono         TEXT,
		direccion        TEXT,
		ciudad           TEXT,
		estado           TEXT,
		pais             TEXT DEFAULT 'Mexico',
		logo             TEXT,
		api_key          TEXT NOT NULL UNIQUE,
		plan             TEXT NOT NULL DEFAULT 'basico',
		max_empleados    INTEGER DEFAULT 25,
		max_dispositivos INTEGER DEFAULT 3,
		activo           INTEGER DEFAULT 1,
		fecha_vence      TEXT,
		fecha_creado     TEXT NOT NULL DEFAULT (datetime('now')),
		db_path          TEXT NOT NULL
	);

	CREATE TABLE IF NOT EXISTS usuarios (
		id            INTEGER PRIMARY KEY AUTOINCREMENT,
		compania_id   INTEGER NOT NULL,
		nombre        TEXT NOT NULL,
		email         TEXT NOT NULL,
		password_hash TEXT NOT NULL,
		rol           TEXT NOT NULL DEFAULT 'readonly',
		sitio_id      INTEGER DEFAULT 0,
		activo        INTEGER DEFAULT 1,
		ultimo_login  TEXT,
		fecha_creado  TEXT NOT NULL DEFAULT (datetime('now')),
		FOREIGN KEY (compania_id) REFERENCES companias(id),
		UNIQUE(compania_id, email)
	);

	CREATE TABLE IF NOT EXISTS sesiones (
		id           INTEGER PRIMARY KEY AUTOINCREMENT,
		usuario_id   INTEGER NOT NULL,
		token        TEXT NOT NULL UNIQUE,
		ip           TEXT,
		user_agent   TEXT,
		creado       TEXT NOT NULL DEFAULT (datetime('now')),
		expira       TEXT NOT NULL,
		activo       INTEGER DEFAULT 1
	);

	CREATE TABLE IF NOT EXISTS auditoria (
		id          INTEGER PRIMARY KEY AUTOINCREMENT,
		compania_id INTEGER,
		usuario_id  INTEGER,
		accion      TEXT NOT NULL,
		tabla       TEXT,
		registro_id INTEGER,
		detalle     TEXT,
		ip          TEXT,
		ts          TEXT NOT NULL DEFAULT (datetime('now'))
	);

	CREATE TABLE IF NOT EXISTS dispositivos (
		id          INTEGER PRIMARY KEY AUTOINCREMENT,
		compania_id INTEGER NOT NULL,
		nombre      TEXT,
		api_key     TEXT NOT NULL,
		ultimo_sync TEXT,
		activo      INTEGER DEFAULT 1,
		fecha_reg   TEXT NOT NULL DEFAULT (datetime('now')),
		FOREIGN KEY (compania_id) REFERENCES companias(id)
	);

	CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
	CREATE INDEX IF NOT EXISTS idx_auditoria_cia  ON auditoria(compania_id);
	`)
	return err
}

// ── BD de compañía ────────────────────────────────────────────
func (m *Manager) CompanyDB(companyID int64) (*sql.DB, error) {
	m.mu.RLock()
	db, ok := m.pool[companyID]
	m.mu.RUnlock()
	if ok {
		return db, nil
	}

	// Buscar path en admin DB
	var dbPath string
	err := m.adminDB.QueryRow("SELECT db_path FROM companias WHERE id=?", companyID).Scan(&dbPath)
	if err != nil {
		return nil, fmt.Errorf("compania %d no encontrada: %w", companyID, err)
	}

	return m.openCompanyDB(companyID, dbPath)
}

func (m *Manager) openCompanyDB(companyID int64, path string) (*sql.DB, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0750); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	if err := migrateCompany(db); err != nil {
		return nil, err
	}

	m.mu.Lock()
	m.pool[companyID] = db
	m.mu.Unlock()
	return db, nil
}

func migrateCompany(db *sql.DB) error {
	_, err := db.Exec(`
	PRAGMA journal_mode=WAL;

	CREATE TABLE IF NOT EXISTS empleados (
		id                    INTEGER PRIMARY KEY AUTOINCREMENT,
		codigo_empleado       TEXT NOT NULL UNIQUE,
		nombre                TEXT NOT NULL,
		puesto                TEXT,
		sitio_trabajo         TEXT,
		seguro_social         TEXT,
		numero_identificacion TEXT,
		telefono              TEXT,
		tipo_sangre           TEXT,
		fecha_alta            TEXT,
		fecha_vencimiento     TEXT,
		foto_url              TEXT,
		activo                INTEGER DEFAULT 1,
		sync_status           INTEGER DEFAULT 0,
		fecha_registro        TEXT NOT NULL DEFAULT (datetime('now'))
	);

	CREATE TABLE IF NOT EXISTS registros (
		id              INTEGER PRIMARY KEY AUTOINCREMENT,
		empleado_id     INTEGER NOT NULL,
		codigo_empleado TEXT NOT NULL,
		nombre_empleado TEXT NOT NULL,
		tipo            TEXT NOT NULL,
		timestamp       TEXT NOT NULL,
		gps_lat         REAL DEFAULT 0,
		gps_lon         REAL DEFAULT 0,
		sitio_trabajo   TEXT,
		metodo          TEXT DEFAULT 'manual',
		notas           TEXT,
		sync_status     INTEGER DEFAULT 1
	);

	CREATE TABLE IF NOT EXISTS sitios (
		id                    INTEGER PRIMARY KEY AUTOINCREMENT,
		nombre                TEXT NOT NULL UNIQUE,
		descripcion           TEXT,
		gps_lat               REAL DEFAULT 0,
		gps_lon               REAL DEFAULT 0,
		geofence_radio_metros REAL DEFAULT 100,
		geofence_tipo         TEXT DEFAULT 'permitido',
		geofence_activo       INTEGER DEFAULT 0,
		tipo_sitio            TEXT DEFAULT 'normal',
		recibir_advertencias  INTEGER DEFAULT 0,
		activo                INTEGER DEFAULT 1
	);

	CREATE TABLE IF NOT EXISTS configuracion (
		id              INTEGER PRIMARY KEY DEFAULT 1,
		nombre_compania TEXT NOT NULL DEFAULT 'Mi Compañía',
		hora_entrada    TEXT DEFAULT '08:00',
		hora_salida     TEXT DEFAULT '17:00',
		tolerancia_min  INTEGER DEFAULT 15
	);

	CREATE INDEX IF NOT EXISTS idx_registros_ts  ON registros(timestamp);
	CREATE INDEX IF NOT EXISTS idx_registros_emp ON registros(codigo_empleado);
	CREATE INDEX IF NOT EXISTS idx_empleados_cod ON empleados(codigo_empleado);
	`)
	return err
}

// CompanyDBByKey obtiene la BD usando el API key del APK
func (m *Manager) CompanyDBByKey(apiKey string) (*sql.DB, int64, error) {
	var id int64
	var dbPath string
	var activo int
	var fechaVence string

	err := m.adminDB.QueryRow(
		"SELECT id, db_path, activo, COALESCE(fecha_vence,'') FROM companias WHERE api_key=?",
		apiKey,
	).Scan(&id, &dbPath, &activo, &fechaVence)
	if err != nil {
		return nil, 0, fmt.Errorf("api_key no válido")
	}
	if activo == 0 {
		return nil, 0, fmt.Errorf("compañía inactiva")
	}

	db, err := m.openCompanyDB(id, dbPath)
	return db, id, err
}

// Audit registra una acción en la tabla auditoria
func (m *Manager) Audit(companyID, userID int64, accion, tabla string, regID int64, detalle, ip string) {
	m.adminDB.Exec(
		`INSERT INTO auditoria(compania_id,usuario_id,accion,tabla,registro_id,detalle,ip) VALUES(?,?,?,?,?,?,?)`,
		companyID, userID, accion, tabla, regID, detalle, ip,
	)
}
