package v1

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"desar-server/internal/auth"
	"desar-server/internal/db"
	"desar-server/internal/models"
	"desar-server/internal/ws"

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
	r.Get("/config",     handlerConfig)
	return r
}

func apiKeyMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		k := r.Header.Get(auth.APIKeyHeader)
		if k == "" {
			jsonErr(w, "X-API-Key requerido", 401); return
		}
		_, compID, err := db.Get().CompanyDBByKey(k)
		if err != nil {
			jsonErr(w, err.Error(), 401); return
		}
		r.Header.Set("X-Company-ID", fmt.Sprintf("%d", compID))
		next.ServeHTTP(w, r)
	})
}

func handlerPing(w http.ResponseWriter, r *http.Request) {
	jsonOK(w, map[string]string{"status":"ok","version":"1.0","ts":time.Now().Format(time.RFC3339)})
}

func handlerSync(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, compID, _ := db.Get().CompanyDBByKey(k)
	var req models.SyncRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		jsonErr(w, "JSON inválido", 400); return
	}
	rs, es := 0, 0
	for _, reg := range req.Registros {
		_, err := compDB.Exec(`INSERT OR IGNORE INTO registros
			(empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,gps_lat,gps_lon,sitio_trabajo,metodo,notas,sync_status)
			VALUES(?,?,?,?,?,?,?,?,?,?,1)`,
			reg.EmpleadoID,reg.CodigoEmpleado,reg.NombreEmpleado,reg.Tipo,
			reg.Timestamp,reg.GPSLat,reg.GPSLon,reg.SitioTrabajo,reg.Metodo,reg.Notas)
		if err == nil {
			rs++
			ws.GetHub().Broadcast(compID, &models.WSEvento{Tipo:"registro",CompaniaID:compID,Datos:reg})
		}
	}
	for _, emp := range req.Empleados {
		compDB.Exec(`INSERT INTO empleados(codigo_empleado,nombre,puesto,sitio_trabajo,activo)
			VALUES(?,?,?,?,?) ON CONFLICT(codigo_empleado) DO UPDATE SET
			nombre=excluded.nombre,puesto=excluded.puesto,activo=excluded.activo`,
			emp.CodigoEmpleado,emp.Nombre,emp.Puesto,emp.SitioTrabajo,emp.Activo)
		es++
	}
	jsonOK(w, models.SyncResponse{OK:true,RegistrosSinc:rs,EmpleadosSinc:es,Timestamp:time.Now().Format(time.RFC3339)})
}

func handlerCrearRegistro(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, compID, _ := db.Get().CompanyDBByKey(k)
	var reg models.Registro
	if err := json.NewDecoder(r.Body).Decode(&reg); err != nil {
		jsonErr(w, "JSON inválido", 400); return
	}
	res, err := compDB.Exec(`INSERT INTO registros
		(empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,gps_lat,gps_lon,sitio_trabajo,metodo,notas,sync_status)
		VALUES(?,?,?,?,?,?,?,?,?,?,1)`,
		reg.EmpleadoID,reg.CodigoEmpleado,reg.NombreEmpleado,reg.Tipo,
		reg.Timestamp,reg.GPSLat,reg.GPSLon,reg.SitioTrabajo,reg.Metodo,reg.Notas)
	if err != nil { jsonErr(w, "error BD", 500); return }
	id, _ := res.LastInsertId()
	reg.ID = id
	ws.GetHub().Broadcast(compID, &models.WSEvento{Tipo:"registro",CompaniaID:compID,Datos:reg})
	jsonOK(w, map[string]int64{"id":id})
}

func handlerSyncEmpleado(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, _, _ := db.Get().CompanyDBByKey(k)
	var emp models.Empleado
	if err := json.NewDecoder(r.Body).Decode(&emp); err != nil {
		jsonErr(w, "JSON inválido", 400); return
	}
	compDB.Exec(`INSERT INTO empleados(codigo_empleado,nombre,puesto,sitio_trabajo,activo,fecha_alta,fecha_vencimiento)
		VALUES(?,?,?,?,?,?,?) ON CONFLICT(codigo_empleado) DO UPDATE SET
		nombre=excluded.nombre,puesto=excluded.puesto,activo=excluded.activo,fecha_vencimiento=excluded.fecha_vencimiento`,
		emp.CodigoEmpleado,emp.Nombre,emp.Puesto,emp.SitioTrabajo,emp.Activo,emp.FechaAlta,emp.FechaVencimiento)
	jsonOK(w, map[string]bool{"ok":true})
}

func handlerListarEmpleados(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, _, _ := db.Get().CompanyDBByKey(k)
	rows, err := compDB.Query("SELECT id,codigo_empleado,nombre,puesto,sitio_trabajo,activo,COALESCE(fecha_vencimiento,'') FROM empleados ORDER BY nombre")
	if err != nil { jsonErr(w, "error BD", 500); return }
	defer rows.Close()
	var lista []models.Empleado
	for rows.Next() {
		var e models.Empleado
		rows.Scan(&e.ID,&e.CodigoEmpleado,&e.Nombre,&e.Puesto,&e.SitioTrabajo,&e.Activo,&e.FechaVencimiento)
		lista = append(lista, e)
	}
	jsonOK(w, lista)
}

func handlerConfig(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, _, _ := db.Get().CompanyDBByKey(k)
	var cfg struct {
		Nombre   string `json:"nombre_compania"`
		Entrada  string `json:"hora_entrada"`
		Salida   string `json:"hora_salida"`
		Toleran  int    `json:"tolerancia_minutos"`
	}
	compDB.QueryRow("SELECT nombre_compania,hora_entrada,hora_salida,tolerancia_min FROM configuracion WHERE id=1").
		Scan(&cfg.Nombre,&cfg.Entrada,&cfg.Salida,&cfg.Toleran)
	jsonOK(w, cfg)
}

func jsonOK(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type","application/json")
	json.NewEncoder(w).Encode(models.APIResp{OK:true,Datos:data})
}
func jsonErr(w http.ResponseWriter, msg string, code int) {
	w.Header().Set("Content-Type","application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(models.APIResp{OK:false,Mensaje:msg})
}
