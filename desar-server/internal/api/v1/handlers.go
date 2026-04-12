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
	r.Get("/ping",       handlerPing)
	r.Post("/sync",      handlerSync)
	r.Post("/registros", handlerCrearRegistro)
	r.Post("/empleados", handlerSyncEmpleado)
	r.Get("/empleados",  handlerListarEmpleados)
	r.Put("/empleados/{id}", handlerActualizarEmpleado)
	r.Delete("/empleados/{id}", handlerEliminarEmpleado)
	r.Get("/config",     handlerConfig)
	return r
}

func q(s string) string { return db.Q(s) }

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

func handlerPing(w http.ResponseWriter, r *http.Request) {
	jsonOK(w, map[string]string{"status": "ok", "version": "2.0", "ts": time.Now().Format(time.RFC3339)})
}

func handlerSync(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
	if err != nil { jsonErr(w, "BD error", 500); return }

	var req models.SyncRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil { jsonErr(w, "JSON inválido", 400); return }

	resp, err := syncsvc.ProcesarSync(compDB, db.Get().AdminDB(), compID, req)
	if err != nil { jsonErr(w, err.Error(), 500); return }
	jsonOK(w, resp)
}

func handlerCrearRegistro(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
	if err != nil { jsonErr(w, "BD error", 500); return }

	var reg models.Registro
	if err := json.NewDecoder(r.Body).Decode(&reg); err != nil { jsonErr(w, "JSON inválido", 400); return }
	if reg.Timestamp == "" { reg.Timestamp = time.Now().Format("2006-01-02T15:04:05") }

	res, err := compDB.Exec(q(`INSERT INTO registros(empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,gps_lat,gps_lon,sitio_trabajo,metodo,notas,sync_status)
		VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,1)`),
		reg.EmpleadoID, reg.CodigoEmpleado, reg.NombreEmpleado, reg.Tipo,
		reg.Timestamp, reg.GPSLat, reg.GPSLon, reg.SitioTrabajo, reg.Metodo, reg.Notas)
	if err != nil { jsonErr(w, "Error al guardar: "+err.Error(), 500); return }
	id, _ := res.LastInsertId()
	reg.ID = id
	jsonOK(w, reg)
}

func handlerSyncEmpleado(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
	if err != nil { jsonErr(w, "BD error", 500); return }

	var emp models.Empleado
	if err := json.NewDecoder(r.Body).Decode(&emp); err != nil { jsonErr(w, "JSON inválido", 400); return }

	var existe int
	compDB.QueryRow(q("SELECT COUNT(*) FROM empleados WHERE codigo_empleado=$1"), emp.CodigoEmpleado).Scan(&existe)
	if existe > 0 {
		compDB.Exec(q(`UPDATE empleados SET nombre=$1,puesto=$2,sitio_trabajo=$3,activo=$4,fecha_vencimiento=$5,sync_status=1
			WHERE codigo_empleado=$6`), emp.Nombre, emp.Puesto, emp.SitioTrabajo, emp.Activo, emp.FechaVencimiento, emp.CodigoEmpleado)
	} else {
		compDB.Exec(q(`INSERT INTO empleados(codigo_empleado,nombre,puesto,sitio_trabajo,activo,fecha_vencimiento,sync_status)
			VALUES($1,$2,$3,$4,$5,$6,1)`), emp.CodigoEmpleado, emp.Nombre, emp.Puesto, emp.SitioTrabajo, emp.Activo, emp.FechaVencimiento)
	}
	jsonOK(w, emp)
}

func handlerActualizarEmpleado(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
	if err != nil { jsonErr(w, "BD error", 500); return }
	cod := chi.URLParam(r, "id")
	var emp models.Empleado
	if err := json.NewDecoder(r.Body).Decode(&emp); err != nil { jsonErr(w, "JSON inválido", 400); return }
	compDB.Exec(q(`UPDATE empleados SET nombre=$1,puesto=$2,sitio_trabajo=$3,activo=$4,
		telefono=$5,rfc=$6,seguro_social=$7,fecha_vencimiento=$8,sync_status=1
		WHERE codigo_empleado=$9`),
		emp.Nombre, emp.Puesto, emp.SitioTrabajo, emp.Activo,
		emp.Telefono, emp.RFC, emp.SeguroSocial, emp.FechaVencimiento, cod)
	jsonOK(w, map[string]bool{"ok": true})
}

func handlerEliminarEmpleado(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
	if err != nil { jsonErr(w, "BD error", 500); return }
	cod := chi.URLParam(r, "id")
	compDB.Exec(q("UPDATE empleados SET activo=0 WHERE codigo_empleado=$1"), cod)
	jsonOK(w, map[string]bool{"ok": true})
}

func handlerListarEmpleados(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
	if err != nil { jsonErr(w, "BD error", 500); return }

	rows, err := compDB.Query(q(`SELECT id,codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),
		activo,COALESCE(fecha_registro,''),COALESCE(fecha_alta,''),COALESCE(fecha_vencimiento,''),sync_status
		FROM empleados WHERE activo=1 ORDER BY nombre`))
	if err != nil { jsonErr(w, "Error BD", 500); return }
	defer rows.Close()

	var lista []models.Empleado
	for rows.Next() {
		var e models.Empleado
		rows.Scan(&e.ID, &e.CodigoEmpleado, &e.Nombre, &e.Puesto, &e.SitioTrabajo,
			&e.Activo, &e.FechaRegistro, &e.FechaAlta, &e.FechaVencimiento, &e.SyncStatus)
		lista = append(lista, e)
	}
	jsonOK(w, lista)
}

func handlerConfig(w http.ResponseWriter, r *http.Request) {
	compID, _ := strconv.ParseInt(r.Header.Get("X-Company-ID"), 10, 64)
	compDB, err := db.Get().CompanyDB(compID)
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

func jsonOK(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.APIResp{OK: true, Datos: data})
}

func jsonErr(w http.ResponseWriter, msg string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(models.APIResp{OK: false, Mensaje: msg})
}
