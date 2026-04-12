package v1

import (
	"encoding/json"
	"fmt"
	"net/http"
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
	jsonOK(w, map[string]string{
		"status": "ok", "version": "1.0",
		"ts": time.Now().Format(time.RFC3339),
	})
}

// POST /api/v1/sync — batch sync con respuesta bidireccional
func handlerSync(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, compID, err := db.Get().CompanyDBByKey(k)
	if err != nil {
		jsonErr(w, err.Error(), 401); return
	}

	var req models.SyncRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		jsonErr(w, "JSON inválido", 400); return
	}

	resp, err := syncsvc.ProcesarSync(compDB, db.Get().AdminDB(), compID, req)
	if err != nil {
		jsonErr(w, "error procesando sync", 500); return
	}
	jsonOK(w, resp)
}

// POST /api/v1/registros — registro individual
func handlerCrearRegistro(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, compID, err := db.Get().CompanyDBByKey(k)
	if err != nil {
		jsonErr(w, err.Error(), 401); return
	}

	var reg models.Registro
	if err := json.NewDecoder(r.Body).Decode(&reg); err != nil {
		jsonErr(w, "JSON inválido", 400); return
	}
	if reg.CodigoEmpleado == "" || reg.Tipo == "" || reg.Timestamp == "" {
		jsonErr(w, "codigo_empleado, tipo y timestamp requeridos", 400); return
	}

	req := models.SyncRequest{Registros: []models.Registro{reg}}
	syncsvc.ProcesarSync(compDB, db.Get().AdminDB(), compID, req)
	jsonOK(w, map[string]bool{"ok": true})
}

// POST /api/v1/empleados
func handlerSyncEmpleado(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, compID, err := db.Get().CompanyDBByKey(k)
	if err != nil {
		jsonErr(w, err.Error(), 401); return
	}

	var emp models.Empleado
	if err := json.NewDecoder(r.Body).Decode(&emp); err != nil {
		jsonErr(w, "JSON inválido", 400); return
	}

	req := models.SyncRequest{Empleados: []models.Empleado{emp}}
	syncsvc.ProcesarSync(compDB, db.Get().AdminDB(), compID, req)
	jsonOK(w, map[string]bool{"ok": true})
}

// GET /api/v1/empleados
func handlerListarEmpleados(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, _, err := db.Get().CompanyDBByKey(k)
	if err != nil {
		jsonErr(w, err.Error(), 401); return
	}

	rows, err := compDB.Query(`SELECT id,codigo_empleado,nombre,puesto,sitio_trabajo,activo,
		COALESCE(fecha_vencimiento,''),COALESCE(fecha_alta,'')
		FROM empleados ORDER BY nombre`)
	if err != nil {
		jsonErr(w, "error BD", 500); return
	}
	defer rows.Close()
	var lista []models.Empleado
	for rows.Next() {
		var e models.Empleado
		rows.Scan(&e.ID, &e.CodigoEmpleado, &e.Nombre, &e.Puesto,
			&e.SitioTrabajo, &e.Activo, &e.FechaVencimiento, &e.FechaAlta)
		lista = append(lista, e)
	}
	jsonOK(w, lista)
}

// GET /api/v1/config
func handlerConfig(w http.ResponseWriter, r *http.Request) {
	k := r.Header.Get(auth.APIKeyHeader)
	compDB, _, err := db.Get().CompanyDBByKey(k)
	if err != nil {
		jsonErr(w, err.Error(), 401); return
	}
	var cfg struct {
		Nombre  string `json:"nombre_compania"`
		Entrada string `json:"hora_entrada"`
		Salida  string `json:"hora_salida"`
		Toleran int    `json:"tolerancia_minutos"`
	}
	compDB.QueryRow(`SELECT nombre_compania,hora_entrada,hora_salida,tolerancia_min
		FROM configuracion WHERE id=1`).
		Scan(&cfg.Nombre, &cfg.Entrada, &cfg.Salida, &cfg.Toleran)
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
