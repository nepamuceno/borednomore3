package models

import "time"

// ── Compañía ─────────────────────────────────────────────────
type Compania struct {
	ID           int64     `json:"id"`
	Nombre       string    `json:"nombre"`
	RFC          string    `json:"rfc"`
	Email        string    `json:"email"`
	Telefono     string    `json:"telefono"`
	Direccion    string    `json:"direccion"`
	Ciudad       string    `json:"ciudad"`
	Estado       string    `json:"estado"`
	Pais         string    `json:"pais"`
	Logo         string    `json:"logo"`
	APIKey       string    `json:"api_key"`
	Plan         string    `json:"plan"` // basico|estandar|enterprise
	MaxEmpleados int       `json:"max_empleados"`
	MaxDispositivos int    `json:"max_dispositivos"`
	Activo       bool      `json:"activo"`
	FechaVence   time.Time `json:"fecha_vence"`
	FechaCreado  time.Time `json:"fecha_creado"`
	DBPath       string    `json:"-"` // ruta a su SQLite
}

// ── Usuario del panel web ─────────────────────────────────────
type Usuario struct {
	ID          int64     `json:"id"`
	CompaniaID  int64     `json:"compania_id"`
	Nombre      string    `json:"nombre"`
	Email       string    `json:"email"`
	PasswordHash string   `json:"-"`
	Rol         string    `json:"rol"` // superadmin|admin|gerente|rrhh|supervisor|readonly
	SitioID     int64     `json:"sitio_id"` // solo para supervisor
	Activo      bool      `json:"activo"`
	UltimoLogin time.Time `json:"ultimo_login"`
	FechaCreado time.Time `json:"fecha_creado"`
}

// ── Empleado (espejo del APK) ─────────────────────────────────
type Empleado struct {
	ID                  int64  `json:"id"`
	CodigoEmpleado      string `json:"codigo_empleado"`
	Nombre              string `json:"nombre"`
	Puesto              string `json:"puesto"`
	SitioTrabajo        string `json:"sitio_trabajo"`
	SeguroSocial        string `json:"seguro_social"`
	NumeroIdentificacion string `json:"numero_identificacion"`
	Telefono            string `json:"telefono"`
	FechaAlta           string `json:"fecha_alta"`
	FechaVencimiento    string `json:"fecha_vencimiento"`
	Activo              int    `json:"activo"`
	FotoURL             string `json:"foto_url"`
	SyncStatus          int    `json:"sync_status"`
}

// ── Registro de asistencia (espejo del APK) ───────────────────
type Registro struct {
	ID             int64   `json:"id"`
	EmpleadoID     int64   `json:"empleado_id"`
	CodigoEmpleado string  `json:"codigo_empleado"`
	NombreEmpleado string  `json:"nombre_empleado"`
	Tipo           string  `json:"tipo"` // entrada|salida
	Timestamp      string  `json:"timestamp"`
	GPSLat         float64 `json:"gps_lat"`
	GPSLon         float64 `json:"gps_lon"`
	SitioTrabajo   string  `json:"sitio_trabajo"`
	Metodo         string  `json:"metodo"` // qr|rostro|manual
	Notas          string  `json:"notas"`
	SyncStatus     int     `json:"sync_status"`
}

// ── Sitio ─────────────────────────────────────────────────────
type Sitio struct {
	ID                  int64   `json:"id"`
	Nombre              string  `json:"nombre"`
	Descripcion         string  `json:"descripcion"`
	GPSLat              float64 `json:"gps_lat"`
	GPSLon              float64 `json:"gps_lon"`
	GeofenceRadioMetros float64 `json:"geofence_radio_metros"`
	GeofenceTipo        string  `json:"geofence_tipo"`
	GeofenceActivo      bool    `json:"geofence_activo"`
	TipoSitio           string  `json:"tipo_sitio"`
	RecibirAdvertencias bool    `json:"recibir_advertencias"`
	Activo              bool    `json:"activo"`
}

// ── Payload JWT ───────────────────────────────────────────────
type Claims struct {
	UserID     int64  `json:"user_id"`
	CompaniaID int64  `json:"compania_id"`
	Rol        string `json:"rol"`
	Email      string `json:"email"`
}

// ── Evento WebSocket ──────────────────────────────────────────
type WSEvento struct {
	Tipo       string      `json:"tipo"` // registro|empleado|alerta
	CompaniaID int64       `json:"compania_id"`
	Datos      interface{} `json:"datos"`
}

// ── Respuesta API ─────────────────────────────────────────────
type APIResp struct {
	OK      bool        `json:"ok"`
	Mensaje string      `json:"mensaje,omitempty"`
	Datos   interface{} `json:"datos,omitempty"`
}

// ── Sync request del APK ──────────────────────────────────────
type SyncRequest struct {
	Registros []Registro `json:"registros"`
	Empleados []Empleado `json:"empleados"`
	Version   string     `json:"version"`
}

type SyncResponse struct {
	OK              bool       `json:"ok"`
	RegistrosSinc   int        `json:"registros_sincronizados"`
	EmpleadosSinc   int        `json:"empleados_sincronizados"`
	EmpleadosNuevos []Empleado `json:"empleados_nuevos,omitempty"`
	Timestamp       string     `json:"timestamp"`
}
