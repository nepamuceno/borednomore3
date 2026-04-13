package v1

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"desar-server/internal/auth"
	"desar-server/internal/db"
	"desar-server/internal/models"
	syncsvc "desar-server/internal/sync"

	"github.com/go-chi/chi/v5"
)

func Router() http.Handler {
	r := chi.NewRouter()
	r.Use(apiKeyMiddleware)

	r.Get("/ping", handlerPing)

	// Sync bidireccional
	r.Post("/sync", handlerSync)

	// Registros
	r.Get("/registros",       handlerListarRegistros)
	r.Post("/registros",      handlerCrearRegistro)
	r.Delete("/registros/{id}", handlerEliminarRegistro)

	// Empleados
	r.Get("/empleados",          handlerListarEmpleados)
	r.Post("/empleados",         handlerSyncEmpleado)
	r.Put("/empleados/{id}",     handlerActualizarEmpleado)
	r.Delete("/empleados/{id}",  handlerEliminarEmpleado)

	// Jornadas (lectura para APK)
	r.Get("/jornadas", handlerListarJornadas)

	// Sitios
	r.Get("/sitios",         handlerListarSitios)
	r.Post("/sitios",        handlerCrearSitio)
	r.Put("/sitios/{id}",    handlerActualizarSitio)
	r.Delete("/sitios/{id}", handlerEliminarSitio)

	// Config
	r.Get("/config", handlerConfig)

	return r
}

func q(s string)  string { return db.Q(s) }
func qi(s string) string { return db.QI(s) }

func apiKeyMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		k := r.Header.Get(auth.APIKeyHeader)
		if k == "" { jsonErr(w, "X-API-Key requerido", 401); return }
		_, compID, err := db.Get().CompanyDBByKey(k)
		if err != nil { jsonErr(w, err.Error(), 401); return }
		r.Header.Set("X-Company-ID", fmt.Sprintf("%d", compID))
		next.ServeHTTP(w, r)
	})
}

func compID(r *http.Request) int64 {
	id, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	return id
}

// ── Ping ──────────────────────────────────────────────────────
func handlerPing(w http.ResponseWriter, r *http.Request) {
	jsonOK(w, map[string]string{"status": "ok", "version": "2.0", "ts": time.Now().Format(time.RFC3339)})
}

// ── Sync completo (APK → servidor y servidor → APK) ───────────
func handlerSync(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	var req models.SyncRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil { jsonErr(w, "JSON inválido: "+err.Error(), 400); return }
	resp, err := syncsvc.ProcesarSync(compDB, db.Get().AdminDB(), cid, req)
	if err != nil { jsonErr(w, err.Error(), 500); return }
	jsonOK(w, resp)
}

// ── Registros ─────────────────────────────────────────────────
func handlerListarRegistros(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }

	desde := r.URL.Query().Get("desde")
	hasta  := r.URL.Query().Get("hasta")
	emp    := r.URL.Query().Get("empleado")
	if desde == "" { desde = time.Now().AddDate(0, 0, -7).Format("2006-01-02") }
	if hasta == ""  { hasta = time.Now().Format("2006-01-02") }

	baseQ := `SELECT id,empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,
		gps_lat,gps_lon,COALESCE(sitio_trabajo,''),COALESCE(metodo,''),COALESCE(notas,''),sync_status
		FROM registros WHERE timestamp >= $1 AND timestamp <= $2`
	args := []interface{}{desde + "T00:00:00", hasta + "T23:59:59"}
	if emp != "" {
		baseQ += " AND (codigo_empleado=$3 OR nombre_empleado LIKE $4)"
		args = append(args, emp, "%"+emp+"%")
	}
	baseQ += " ORDER BY timestamp DESC LIMIT 1000"

	rows, err := compDB.Query(q(baseQ), args...)
	if err != nil { jsonErr(w, "Error BD: "+err.Error(), 500); return }
	defer rows.Close()

	var lista []models.Registro
	for rows.Next() {
		var reg models.Registro
		rows.Scan(&reg.ID, &reg.EmpleadoID, &reg.CodigoEmpleado, &reg.NombreEmpleado,
			&reg.Tipo, &reg.Timestamp, &reg.GPSLat, &reg.GPSLon,
			&reg.SitioTrabajo, &reg.Metodo, &reg.Notas, &reg.SyncStatus)
		lista = append(lista, reg)
	}
	jsonOK(w, lista)
}

func handlerCrearRegistro(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	var reg models.Registro
	if err := json.NewDecoder(r.Body).Decode(&reg); err != nil { jsonErr(w, "JSON inválido", 400); return }
	if reg.Timestamp == "" { reg.Timestamp = time.Now().Format("2006-01-02T15:04:05") }
	if reg.CodigoEmpleado == "" { jsonErr(w, "codigo_empleado requerido", 400); return }
	if reg.Tipo != "entrada" && reg.Tipo != "salida" { jsonErr(w, "tipo debe ser entrada o salida", 400); return }

	// Obtener nombre si falta
	if reg.NombreEmpleado == "" {
		compDB.QueryRow(q("SELECT nombre FROM empleados WHERE codigo_empleado=$1"), reg.CodigoEmpleado).Scan(&reg.NombreEmpleado)
	}
	// Obtener empleado_id si falta
	if reg.EmpleadoID == 0 {
		compDB.QueryRow(q("SELECT id FROM empleados WHERE codigo_empleado=$1"), reg.CodigoEmpleado).Scan(&reg.EmpleadoID)
	}

	res, err := compDB.Exec(q(`INSERT INTO registros(empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,gps_lat,gps_lon,sitio_trabajo,metodo,notas,sync_status)
		VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,1)`),
		reg.EmpleadoID, reg.CodigoEmpleado, reg.NombreEmpleado, reg.Tipo,
		reg.Timestamp, reg.GPSLat, reg.GPSLon, reg.SitioTrabajo, reg.Metodo, reg.Notas)
	if err != nil { jsonErr(w, "Error guardar: "+err.Error(), 500); return }
	id, _ := res.LastInsertId()
	reg.ID = id
	jsonOK(w, reg)
}

func handlerEliminarRegistro(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB.Exec(q("DELETE FROM registros WHERE id=$1"), id)
	jsonOK(w, map[string]bool{"ok": true})
}

// ── Empleados ─────────────────────────────────────────────────
func handlerListarEmpleados(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }

	soloActivos := r.URL.Query().Get("activo") != "0"
	baseQ := `SELECT id,codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),
		activo,COALESCE(fecha_registro,''),COALESCE(fecha_alta,''),COALESCE(fecha_vencimiento,''),sync_status
		FROM empleados`
	if soloActivos { baseQ += " WHERE activo=1" }
	baseQ += " ORDER BY nombre"

	rows, err := compDB.Query(q(baseQ))
	if err != nil { jsonErr(w, "Error BD", 500); return }
	defer rows.Close()

	var lista []models.Empleado
	for rows.Next() {
		var e models.Empleado
		rows.Scan(&e.ID, &e.CodigoEmpleado, &e.Nombre, &e.Puesto, &e.SitioTrabajo,
			&e.Activo, &e.FechaRegistro, &e.FechaAlta, &e.FechaVencimiento, &e.SyncStatus)
		lista = append(lista, e)
	}
	if lista == nil { lista = []models.Empleado{} }
	jsonOK(w, lista)
}

func handlerSyncEmpleado(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	var emp models.Empleado
	if err := json.NewDecoder(r.Body).Decode(&emp); err != nil { jsonErr(w, "JSON inválido", 400); return }
	if emp.CodigoEmpleado == "" { jsonErr(w, "codigo_empleado requerido", 400); return }

	var existe int
	compDB.QueryRow(q("SELECT COUNT(*) FROM empleados WHERE codigo_empleado=$1"), emp.CodigoEmpleado).Scan(&existe)
	if existe > 0 {
		compDB.Exec(q(`UPDATE empleados SET nombre=$1,puesto=$2,sitio_trabajo=$3,activo=$4,
			telefono=$5,rfc=$6,seguro_social=$7,fecha_alta=$8,fecha_vencimiento=$9,
			direccion=$10,ciudad=$11,estado=$12,codigo_postal=$13,telefono_emergencia=$14,
			fecha_nacimiento=$15,tipo_sangre=$16,notas=$17,sync_status=1 WHERE codigo_empleado=$18`),
			emp.Nombre, emp.Puesto, emp.SitioTrabajo, emp.Activo,
			emp.Telefono, emp.RFC, emp.SeguroSocial, emp.FechaAlta, emp.FechaVencimiento,
			emp.Direccion, emp.Ciudad, emp.Estado, emp.CodigoPostal, emp.TelefonoEmergencia,
			emp.FechaNacimiento, emp.TipoSangre, emp.Notas, emp.CodigoEmpleado)
	} else {
		compDB.Exec(q(`INSERT INTO empleados(codigo_empleado,nombre,puesto,sitio_trabajo,activo,
			telefono,rfc,seguro_social,fecha_alta,fecha_vencimiento,
			direccion,ciudad,estado,codigo_postal,telefono_emergencia,
			fecha_nacimiento,tipo_sangre,notas,sync_status)
			VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,1)`),
			emp.CodigoEmpleado, emp.Nombre, emp.Puesto, emp.SitioTrabajo, emp.Activo,
			emp.Telefono, emp.RFC, emp.SeguroSocial, emp.FechaAlta, emp.FechaVencimiento,
			emp.Direccion, emp.Ciudad, emp.Estado, emp.CodigoPostal, emp.TelefonoEmergencia,
			emp.FechaNacimiento, emp.TipoSangre, emp.Notas)
	}
	jsonOK(w, emp)
}

func handlerActualizarEmpleado(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	cod := chi.URLParam(r, "id")
	var emp models.Empleado
	if err := json.NewDecoder(r.Body).Decode(&emp); err != nil { jsonErr(w, "JSON inválido", 400); return }
	compDB.Exec(q(`UPDATE empleados SET nombre=$1,puesto=$2,sitio_trabajo=$3,activo=$4,
		telefono=$5,rfc=$6,seguro_social=$7,fecha_vencimiento=$8,
		direccion=$9,ciudad=$10,estado=$11,codigo_postal=$12,
		telefono_emergencia=$13,fecha_nacimiento=$14,tipo_sangre=$15,notas=$16,
		foto_perfil=$17,foto_rostro_1=$18,foto_rostro_2=$19,foto_rostro_3=$20,
		embedding_1=$21,embedding_2=$22,embedding_3=$23,sync_status=1
		WHERE codigo_empleado=$24`),
		emp.Nombre, emp.Puesto, emp.SitioTrabajo, emp.Activo,
		emp.Telefono, emp.RFC, emp.SeguroSocial, emp.FechaVencimiento,
		emp.Direccion, emp.Ciudad, emp.Estado, emp.CodigoPostal,
		emp.TelefonoEmergencia, emp.FechaNacimiento, emp.TipoSangre, emp.Notas,
		emp.FotoPerfil, emp.FotoRostro1, emp.FotoRostro2, emp.FotoRostro3,
		emp.Embedding1, emp.Embedding2, emp.Embedding3, cod)
	jsonOK(w, map[string]bool{"ok": true})
}

func handlerEliminarEmpleado(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	cod := chi.URLParam(r, "id")
	compDB.Exec(q("UPDATE empleados SET activo=0 WHERE codigo_empleado=$1"), cod)
	jsonOK(w, map[string]bool{"ok": true})
}

// ── Sitios ────────────────────────────────────────────────────
func handlerListarSitios(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	rows, err := compDB.Query("SELECT id,nombre,COALESCE(descripcion,''),gps_lat,gps_lon,geofence_radio_metros,COALESCE(geofence_tipo,'permitido'),geofence_activo,COALESCE(tipo_sitio,'normal'),recibir_advertencias,activo FROM sitios WHERE activo=1 ORDER BY nombre")
	if err != nil { jsonErr(w, "Error BD", 500); return }
	defer rows.Close()
	var lista []models.Sitio
	for rows.Next() {
		var s models.Sitio
		rows.Scan(&s.ID, &s.Nombre, &s.Descripcion, &s.GPSLat, &s.GPSLon,
			&s.GeofenceRadioMetros, &s.GeofenceTipo, &s.GeofenceActivo,
			&s.TipoSitio, &s.RecibirAdvertencias, &s.Activo)
		lista = append(lista, s)
	}
	if lista == nil { lista = []models.Sitio{} }
	jsonOK(w, lista)
}

func handlerCrearSitio(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	var s models.Sitio
	if err := json.NewDecoder(r.Body).Decode(&s); err != nil { jsonErr(w, "JSON inválido", 400); return }
	if s.Nombre == "" { jsonErr(w, "nombre requerido", 400); return }
	if s.GeofenceTipo == "" { s.GeofenceTipo = "permitido" }
	if s.TipoSitio == "" { s.TipoSitio = "normal" }
	res, err := compDB.Exec(q(`INSERT INTO sitios(nombre,descripcion,gps_lat,gps_lon,geofence_radio_metros,geofence_tipo,geofence_activo,tipo_sitio,recibir_advertencias,activo)
		VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,1)`),
		s.Nombre, s.Descripcion, s.GPSLat, s.GPSLon, s.GeofenceRadioMetros,
		s.GeofenceTipo, boolInt(s.GeofenceActivo), s.TipoSitio, boolInt(s.RecibirAdvertencias))
	if err != nil { jsonErr(w, "Error guardar: "+err.Error(), 500); return }
	id, _ := res.LastInsertId()
	s.ID = id
	jsonOK(w, s)
}

func handlerActualizarSitio(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	var s models.Sitio
	if err := json.NewDecoder(r.Body).Decode(&s); err != nil { jsonErr(w, "JSON inválido", 400); return }
	compDB.Exec(q(`UPDATE sitios SET nombre=$1,descripcion=$2,gps_lat=$3,gps_lon=$4,
		geofence_radio_metros=$5,geofence_tipo=$6,geofence_activo=$7,
		tipo_sitio=$8,recibir_advertencias=$9,activo=$10 WHERE id=$11`),
		s.Nombre, s.Descripcion, s.GPSLat, s.GPSLon, s.GeofenceRadioMetros,
		s.GeofenceTipo, boolInt(s.GeofenceActivo), s.TipoSitio, boolInt(s.RecibirAdvertencias), boolInt(s.Activo), id)
	jsonOK(w, map[string]bool{"ok": true})
}

func handlerEliminarSitio(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB.Exec(q("UPDATE sitios SET activo=0 WHERE id=$1"), id)
	jsonOK(w, map[string]bool{"ok": true})
}

// ── Jornadas (APK recibe sus jornadas) ───────────────────────
func handlerListarJornadas(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }

	desde := r.URL.Query().Get("desde")
	hasta  := r.URL.Query().Get("hasta")
	emp    := r.URL.Query().Get("empleado")
	if desde == "" { desde = time.Now().AddDate(0, 0, -30).Format("2006-01-02") }
	if hasta == ""  { hasta = time.Now().Format("2006-01-02") }

	type Jornada struct {
		ID               int64   `json:"id"`
		EmpleadoID       int64   `json:"empleado_id"`
		CodigoEmpleado   string  `json:"codigo_empleado"`
		NombreEmpleado   string  `json:"nombre_empleado"`
		Fecha            string  `json:"fecha"`
		EntradaTimestamp string  `json:"entrada_timestamp"`
		SalidaTimestamp  string  `json:"salida_timestamp"`
		HorasTrabajadas  float64 `json:"horas_trabajadas"`
		Completa         int     `json:"completa"`
		SitioTrabajo     string  `json:"sitio_trabajo"`
	}

	baseQ := `SELECT id,empleado_id,codigo_empleado,nombre_empleado,fecha,
		COALESCE(entrada_timestamp,''),COALESCE(salida_timestamp,''),
		COALESCE(horas_trabajadas,0),completa,COALESCE(sitio_trabajo,'')
		FROM jornadas WHERE fecha >= $1 AND fecha <= $2`
	args := []interface{}{desde, hasta}
	if emp != "" {
		baseQ += " AND (codigo_empleado=$3 OR nombre_empleado LIKE $4)"
		args = append(args, emp, "%"+emp+"%")
	}
	baseQ += " ORDER BY fecha DESC, nombre_empleado ASC LIMIT 2000"

	rows, err := compDB.Query(q(baseQ), args...)
	if err != nil { jsonErr(w, "Error BD: "+err.Error(), 500); return }
	defer rows.Close()

	var lista []Jornada
	for rows.Next() {
		var j Jornada
		rows.Scan(&j.ID, &j.EmpleadoID, &j.CodigoEmpleado, &j.NombreEmpleado,
			&j.Fecha, &j.EntradaTimestamp, &j.SalidaTimestamp,
			&j.HorasTrabajadas, &j.Completa, &j.SitioTrabajo)
		lista = append(lista, j)
	}
	if lista == nil { lista = []Jornada{} }
	jsonOK(w, lista)
}

// ── Config ────────────────────────────────────────────────────
func handlerConfig(w http.ResponseWriter, r *http.Request) {
	cid := compID(r)
	compDB, err := db.Get().CompanyDB(cid)
	if err != nil { jsonErr(w, "BD error", 500); return }
	var cfg models.Configuracion
	compDB.QueryRow(`SELECT nombre_compania,COALESCE(zona_horaria,'America/Mexico_City'),
		COALESCE(hora_entrada_default,'08:00'),COALESCE(hora_salida_default,'17:00'),
		tolerancia_minutos,jornada_horas,umbral_reconocimiento
		FROM configuracion WHERE id=1`).Scan(
		&cfg.NombreCompania, &cfg.ZonaHoraria,
		&cfg.HoraEntradaDefault, &cfg.HoraSalidaDefault,
		&cfg.ToleranciaMinutos, &cfg.JornadaHoras, &cfg.UmbralReconocimiento)
	jsonOK(w, cfg)
}

// ── Helpers ───────────────────────────────────────────────────
func boolInt(b bool) int { if b { return 1 }; return 0 }

func jsonOK(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.APIResp{OK: true, Datos: data})
}

func jsonErr(w http.ResponseWriter, msg string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(models.APIResp{OK: false, Mensaje: msg})
}
