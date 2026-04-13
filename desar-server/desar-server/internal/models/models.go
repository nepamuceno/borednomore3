package models

import "time"

// ── Compañía ─────────────────────────────────────────────────
type Compania struct {
	ID              int64     `json:"id"`
	Nombre          string    `json:"nombre"`
	RFC             string    `json:"rfc"`
	Email           string    `json:"email"`
	Telefono        string    `json:"telefono"`
	Direccion       string    `json:"direccion"`
	Ciudad          string    `json:"ciudad"`
	Estado          string    `json:"estado"`
	Pais            string    `json:"pais"`
	Logo            string    `json:"logo"`
	APIKey          string    `json:"api_key"`
	Plan            string    `json:"plan"` // basico|estandar|enterprise
	MaxEmpleados    int       `json:"max_empleados"`
	MaxDispositivos int       `json:"max_dispositivos"`
	Activo          bool      `json:"activo"`
	FechaVence      time.Time `json:"fecha_vence"`
	FechaCreado     time.Time `json:"fecha_creado"`
	DBPath          string    `json:"-"`
}

// ── Usuario del panel web ─────────────────────────────────────
type Usuario struct {
	ID           int64     `json:"id"`
	CompaniaID   int64     `json:"compania_id"`
	Nombre       string    `json:"nombre"`
	Email        string    `json:"email"`
	PasswordHash string    `json:"-"`
	Rol          string    `json:"rol"` // superadmin|admin|gerente|rrhh|supervisor|readonly
	SitioID      int64     `json:"sitio_id"`
	Activo       bool      `json:"activo"`
	UltimoLogin  time.Time `json:"ultimo_login"`
	FechaCreado  time.Time `json:"fecha_creado"`
}

// ── Empleado — todos los campos del APK + sync ────────────────
type Empleado struct {
	ID                   int64  `json:"id"`
	CodigoEmpleado       string `json:"codigo_empleado"`
	Nombre               string `json:"nombre"`
	Direccion            string `json:"direccion"`
	Ciudad               string `json:"ciudad"`
	Estado               string `json:"estado"`
	Pais                 string `json:"pais"`
	CodigoPostal         string `json:"codigo_postal"`
	Telefono             string `json:"telefono"`
	TelefonoEmergencia   string `json:"telefono_emergencia"`
	FechaNacimiento      string `json:"fecha_nacimiento"`
	RFC                  string `json:"rfc"`
	SeguroSocial         string `json:"seguro_social"`
	NumeroIdentificacion string `json:"numero_identificacion"`
	Puesto               string `json:"puesto"`
	TipoSangre           string `json:"tipo_sangre"`
	Notas                string `json:"notas"`
	FotoPerfil           string `json:"foto_perfil"`
	FotoRostro1          string `json:"foto_rostro_1"`
	FotoRostro2          string `json:"foto_rostro_2"`
	FotoRostro3          string `json:"foto_rostro_3"`
	Embedding1           string `json:"embedding_1"`
	Embedding2           string `json:"embedding_2"`
	Embedding3           string `json:"embedding_3"`
	SitioTrabajo         string `json:"sitio_trabajo"`
	Activo               int    `json:"activo"`
	FechaRegistro        string `json:"fecha_registro"`
	FechaAlta            string `json:"fecha_alta"`
	FechaVencimiento     string `json:"fecha_vencimiento"`
	SyncStatus           int    `json:"sync_status"`
}

// ── Registro de asistencia — todos los campos del APK ─────────
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

// ── Sitio — todos los campos del APK ─────────────────────────
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

// ── Sync request/response del APK ────────────────────────────
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

// ── Registro de autoregistro (landing) ───────────────────────
type RegistroCompania struct {
	NombreCompania string `json:"nombre_compania"`
	NombreAdmin    string `json:"nombre_admin"`
	Email          string `json:"email"`
	Password       string `json:"password"`
	Telefono       string `json:"telefono"`
}

// ── Configuración (para API APK) ──────────────────────────────
type Configuracion struct {
	NombreCompania       string  `json:"nombre_compania"`
	ZonaHoraria          string  `json:"zona_horaria"`
	HoraEntradaDefault   string  `json:"hora_entrada_default"`
	HoraSalidaDefault    string  `json:"hora_salida_default"`
	ToleranciaMinutos    int     `json:"tolerancia_minutos"`
	JornadaHoras         float64 `json:"jornada_horas"`
	UmbralReconocimiento float64 `json:"umbral_reconocimiento"`
}
