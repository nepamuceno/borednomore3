package web

import (
	"database/sql"
	"encoding/json"
	"html/template"
	"net/http"
	"strconv"
	"time"

	"desar-server/internal/auth"
	"desar-server/internal/db"
	"desar-server/internal/models"
	"desar-server/internal/ws"

	"github.com/go-chi/chi/v5"
)

var tmpl *template.Template

func Init(t *template.Template) {
	tmpl = t
}

func Router() http.Handler {
	r := chi.NewRouter()

	// Rutas públicas
	r.Get("/login",  handlerLoginGet)
	r.Post("/login", handlerLoginPost)
	r.Get("/logout", handlerLogout)

	// Rutas protegidas
	r.Group(func(r chi.Router) {
		r.Use(auth.MiddlewareWeb)
		r.Get("/",            handlerDashboard)
		r.Get("/ws",          handlerWS)
		r.Get("/empleados",   handlerEmpleados)
		r.Get("/registros",   handlerRegistros)
		r.Get("/registros/hoy", handlerRegistrosHoy)
		r.Get("/sitios",      handlerSitios)
		r.Get("/config",      handlerConfig)
		r.Post("/config",     handlerConfigSave)
		r.Get("/reportes",    handlerReportes)
		r.Get("/usuarios",    handlerUsuarios)
		r.Post("/usuarios",   handlerUsuarioCrear)
		r.Delete("/usuarios/{id}", handlerUsuarioEliminar)
	})

	// Superadmin
	r.Group(func(r chi.Router) {
		r.Use(auth.MiddlewareWeb)
		r.Use(auth.RequierePermiso("companias.ver"))
		r.Get("/sa/companias",      handlerSACompanias)
		r.Post("/sa/companias",     handlerSACrearCompania)
		r.Get("/sa/companias/{id}", handlerSACompaniaDetalle)
		r.Put("/sa/companias/{id}/toggle", handlerSAToggleCompania)
	})

	return r
}

// ── Login ─────────────────────────────────────────────────────
func handlerLoginGet(w http.ResponseWriter, r *http.Request) {
	render(w, "auth/login.html", map[string]interface{}{"Error": r.URL.Query().Get("e")})
}

func handlerLoginPost(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	email := r.FormValue("email")
	password := r.FormValue("password")

	adminDB := db.Get().AdminDB()
	var u models.Usuario
	var pwHash string
	err := adminDB.QueryRow(`
		SELECT id,compania_id,nombre,email,password_hash,rol,activo
		FROM usuarios WHERE email=? AND activo=1`, email).
		Scan(&u.ID, &u.CompaniaID, &u.Nombre, &u.Email, &pwHash, &u.Rol, &u.Activo)
	if err != nil || !auth.VerificarPassword(pwHash, password) {
		http.Redirect(w, r, "/desar/login?e=credenciales+incorrectas", http.StatusFound)
		return
	}

	token, err := auth.GenerarToken(&u)
	if err != nil {
		http.Redirect(w, r, "/desar/login?e=error+interno", http.StatusFound)
		return
	}

	adminDB.Exec("UPDATE usuarios SET ultimo_login=? WHERE id=?", time.Now().Format(time.RFC3339), u.ID)
	db.Get().Audit(u.CompaniaID, u.ID, "login", "usuarios", u.ID, "login exitoso", r.RemoteAddr)

	auth.SetCookie(w, token)
	http.Redirect(w, r, "/desar/", http.StatusFound)
}

func handlerLogout(w http.ResponseWriter, r *http.Request) {
	auth.ClearCookie(w)
	http.Redirect(w, r, "/desar/login", http.StatusFound)
}

// ── Dashboard ─────────────────────────────────────────────────
func handlerDashboard(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, err := db.Get().CompanyDB(claims.CompaniaID)
	if err != nil {
		http.Error(w, "BD no disponible", 500); return
	}

	data := dashboardData(compDB, claims)
	render(w, "admin/dashboard.html", data)
}

func dashboardData(compDB *sql.DB, claims *models.Claims) map[string]interface{} {
	hoy := time.Now().Format("2006-01-02")

	var totalEmp, presentes, salidas, regHoy int
	compDB.QueryRow("SELECT COUNT(*) FROM empleados WHERE activo=1").Scan(&totalEmp)
	compDB.QueryRow(`SELECT COUNT(*) FROM registros WHERE timestamp LIKE ?`, hoy+"%").Scan(&regHoy)
	compDB.QueryRow(`SELECT COUNT(*) FROM (
		SELECT codigo_empleado FROM registros WHERE timestamp LIKE ? AND tipo='entrada'
		EXCEPT
		SELECT codigo_empleado FROM registros WHERE timestamp LIKE ? AND tipo='salida'
	)`, hoy+"%", hoy+"%").Scan(&presentes)
	compDB.QueryRow(`SELECT COUNT(DISTINCT codigo_empleado) FROM registros WHERE timestamp LIKE ? AND tipo='salida'`, hoy+"%").Scan(&salidas)

	// Últimos 20 registros hoy
	rows, _ := compDB.Query(`SELECT codigo_empleado,nombre_empleado,tipo,timestamp,sitio_trabajo,metodo
		FROM registros WHERE timestamp LIKE ? ORDER BY timestamp DESC LIMIT 20`, hoy+"%")
	var ultimos []models.Registro
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var reg models.Registro
			rows.Scan(&reg.CodigoEmpleado,&reg.NombreEmpleado,&reg.Tipo,&reg.Timestamp,&reg.SitioTrabajo,&reg.Metodo)
			ultimos = append(ultimos, reg)
		}
	}

	return map[string]interface{}{
		"Claims":     claims,
		"TotalEmp":   totalEmp,
		"Presentes":  presentes,
		"Salidas":    salidas,
		"RegHoy":     regHoy,
		"Ultimos":    ultimos,
		"Conectados": ws.GetHub().ConnectedCount(claims.CompaniaID),
		"Hoy":        hoy,
	}
}

// ── WebSocket ─────────────────────────────────────────────────
func handlerWS(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	ws.Handler(w, r, claims.CompaniaID)
}

// ── Empleados ─────────────────────────────────────────────────
func handlerEmpleados(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.ver") {
		http.Error(w, "403", 403); return
	}
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	rows, _ := compDB.Query(`SELECT id,codigo_empleado,nombre,puesto,sitio_trabajo,activo,
		COALESCE(fecha_vencimiento,''),COALESCE(fecha_alta,'') FROM empleados ORDER BY nombre`)
	var lista []models.Empleado
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var e models.Empleado
			rows.Scan(&e.ID,&e.CodigoEmpleado,&e.Nombre,&e.Puesto,&e.SitioTrabajo,&e.Activo,&e.FechaVencimiento,&e.FechaAlta)
			lista = append(lista, e)
		}
	}
	render(w, "admin/empleados.html", map[string]interface{}{"Claims":claims,"Empleados":lista})
}

// ── Registros ─────────────────────────────────────────────────
func handlerRegistros(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde")
	hasta := r.URL.Query().Get("hasta")
	emp   := r.URL.Query().Get("emp")
	if desde == "" { desde = time.Now().AddDate(0, 0, -7).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }

	query := `SELECT codigo_empleado,nombre_empleado,tipo,timestamp,sitio_trabajo,metodo,COALESCE(notas,'')
		FROM registros WHERE timestamp >= ? AND timestamp <= ?`
	args := []interface{}{desde + "T00:00:00", hasta + "T23:59:59"}
	if emp != "" {
		query += " AND codigo_empleado=?"
		args = append(args, emp)
	}
	query += " ORDER BY timestamp DESC LIMIT 500"

	rows, _ := compDB.Query(query, args...)
	var lista []models.Registro
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var reg models.Registro
			rows.Scan(&reg.CodigoEmpleado,&reg.NombreEmpleado,&reg.Tipo,&reg.Timestamp,&reg.SitioTrabajo,&reg.Metodo,&reg.Notas)
			lista = append(lista, reg)
		}
	}
	render(w, "admin/registros.html", map[string]interface{}{
		"Claims":claims,"Registros":lista,"Desde":desde,"Hasta":hasta,"EmpFiltro":emp,
	})
}

// ── Registros HOY (JSON para AJAX/WS) ────────────────────────
func handlerRegistrosHoy(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	hoy := time.Now().Format("2006-01-02")
	rows, _ := compDB.Query(`SELECT codigo_empleado,nombre_empleado,tipo,timestamp,sitio_trabajo,metodo
		FROM registros WHERE timestamp LIKE ? ORDER BY timestamp DESC`, hoy+"%")
	var lista []models.Registro
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var reg models.Registro
			rows.Scan(&reg.CodigoEmpleado,&reg.NombreEmpleado,&reg.Tipo,&reg.Timestamp,&reg.SitioTrabajo,&reg.Metodo)
			lista = append(lista, reg)
		}
	}
	w.Header().Set("Content-Type","application/json")
	json.NewEncoder(w).Encode(lista)
}

// ── Sitios ────────────────────────────────────────────────────
func handlerSitios(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	rows, _ := compDB.Query("SELECT id,nombre,COALESCE(descripcion,''),gps_lat,gps_lon,tipo_sitio,geofence_activo,recibir_advertencias FROM sitios WHERE activo=1")
	var lista []models.Sitio
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var s models.Sitio
			rows.Scan(&s.ID,&s.Nombre,&s.Descripcion,&s.GPSLat,&s.GPSLon,&s.TipoSitio,&s.GeofenceActivo,&s.RecibirAdvertencias)
			lista = append(lista, s)
		}
	}
	render(w, "admin/sitios.html", map[string]interface{}{"Claims":claims,"Sitios":lista})
}

// ── Config ────────────────────────────────────────────────────
func handlerConfig(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "config.ver") {
		http.Error(w, "403", 403); return
	}
	adminDB := db.Get().AdminDB()
	var c models.Compania
	adminDB.QueryRow("SELECT id,nombre,rfc,email,telefono,ciudad,estado,plan,max_empleados,fecha_vence FROM companias WHERE id=?",
		claims.CompaniaID).Scan(&c.ID,&c.Nombre,&c.RFC,&c.Email,&c.Telefono,&c.Ciudad,&c.Estado,&c.Plan,&c.MaxEmpleados,&c.FechaVence)
	render(w, "admin/config.html", map[string]interface{}{"Claims":claims,"Compania":c,"Ok":r.URL.Query().Get("ok")})
}

func handlerConfigSave(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "config.editar") {
		http.Error(w, "403", 403); return
	}
	r.ParseForm()
	db.Get().AdminDB().Exec("UPDATE companias SET nombre=?,rfc=?,email=?,telefono=?,ciudad=?,estado=? WHERE id=?",
		r.FormValue("nombre"),r.FormValue("rfc"),r.FormValue("email"),r.FormValue("telefono"),
		r.FormValue("ciudad"),r.FormValue("estado"),claims.CompaniaID)
	db.Get().Audit(claims.CompaniaID,claims.UserID,"update","companias",claims.CompaniaID,"config actualizada",r.RemoteAddr)
	http.Redirect(w, r, "/desar/config?ok=1", http.StatusFound)
}

// ── Usuarios del panel ────────────────────────────────────────
func handlerUsuarios(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.ver") {
		http.Error(w, "403", 403); return
	}
	rows, _ := db.Get().AdminDB().Query(
		"SELECT id,nombre,email,rol,activo,COALESCE(ultimo_login,'') FROM usuarios WHERE compania_id=? ORDER BY nombre",
		claims.CompaniaID)
	var lista []models.Usuario
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var u models.Usuario
			rows.Scan(&u.ID,&u.Nombre,&u.Email,&u.Rol,&u.Activo,&u.UltimoLogin)
			lista = append(lista, u)
		}
	}
	roles := []string{"admin","gerente","rrhh","supervisor","readonly"}
	render(w, "admin/usuarios.html", map[string]interface{}{"Claims":claims,"Usuarios":lista,"Roles":roles})
}

func handlerUsuarioCrear(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.crear") {
		http.Error(w, "403", 403); return
	}
	r.ParseForm()
	hash, _ := auth.HashPassword(r.FormValue("password"))
	db.Get().AdminDB().Exec(`INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES(?,?,?,?,?)`,
		claims.CompaniaID,r.FormValue("nombre"),r.FormValue("email"),hash,r.FormValue("rol"))
	db.Get().Audit(claims.CompaniaID,claims.UserID,"create","usuarios",0,"usuario creado: "+r.FormValue("email"),r.RemoteAddr)
	http.Redirect(w, r, "/desar/usuarios?ok=1", http.StatusFound)
}

func handlerUsuarioEliminar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r,"id"), 10, 64)
	db.Get().AdminDB().Exec("UPDATE usuarios SET activo=0 WHERE id=? AND compania_id=?", id, claims.CompaniaID)
	w.WriteHeader(204)
}

// ── Superadmin: compañías ─────────────────────────────────────
func handlerSACompanias(w http.ResponseWriter, r *http.Request) {
	rows, _ := db.Get().AdminDB().Query(
		"SELECT id,nombre,email,plan,activo,max_empleados,fecha_vence,fecha_creado,api_key FROM companias ORDER BY nombre")
	var lista []models.Compania
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var c models.Compania
			rows.Scan(&c.ID,&c.Nombre,&c.Email,&c.Plan,&c.Activo,&c.MaxEmpleados,&c.FechaVence,&c.FechaCreado,&c.APIKey)
			lista = append(lista, c)
		}
	}
	render(w, "superadmin/companias.html", map[string]interface{}{
		"Claims":auth.ClaimsFromCtx(r),"Companias":lista,
	})
}

func handlerSACrearCompania(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	apiKey := auth.GenerarAPIKey()
	nombre := r.FormValue("nombre")
	plan   := r.FormValue("plan")
	if plan == "" { plan = "basico" }
	maxEmp := 25
	if plan == "estandar" { maxEmp = 100 } else if plan == "enterprise" { maxEmp = 9999 }

	dbPath := db.Get().AdminDB()
	var dbsPath string
	dbPath.QueryRow("SELECT db_path FROM companias LIMIT 1").Scan(&dbsPath)
	// Use a simulated path
	compDBPath := "./data/companies/" + apiKey + ".db"

	res, err := db.Get().AdminDB().Exec(`INSERT INTO companias
		(nombre,rfc,email,api_key,plan,max_empleados,max_dispositivos,activo,fecha_vence,db_path)
		VALUES(?,?,?,?,?,?,3,1,?,?)`,
		nombre,r.FormValue("rfc"),r.FormValue("email"),apiKey,plan,maxEmp,
		r.FormValue("fecha_vence"),compDBPath)
	if err != nil {
		http.Error(w, "Error: "+err.Error(), 500); return
	}
	compID, _ := res.LastInsertId()

	// Crear admin inicial de la compañía
	pw := r.FormValue("admin_password")
	if pw == "" { pw = "admin123" }
	hash, _ := auth.HashPassword(pw)
	db.Get().AdminDB().Exec(`INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol)
		VALUES(?,?,?,?,'admin')`,
		compID,r.FormValue("admin_nombre"),r.FormValue("admin_email"),hash)

	// Inicializar la BD de la compañía
	db.Get().CompanyDB(compID)

	claims := auth.ClaimsFromCtx(r)
	db.Get().Audit(0,claims.UserID,"create","companias",compID,"nueva compañía: "+nombre,r.RemoteAddr)
	http.Redirect(w, r, "/desar/sa/companias?ok="+nombre, http.StatusFound)
}

func handlerSACompaniaDetalle(w http.ResponseWriter, r *http.Request) {
	id, _ := strconv.ParseInt(chi.URLParam(r,"id"), 10, 64)
	var c models.Compania
	db.Get().AdminDB().QueryRow("SELECT id,nombre,email,plan,activo,api_key,max_empleados,fecha_vence FROM companias WHERE id=?",id).
		Scan(&c.ID,&c.Nombre,&c.Email,&c.Plan,&c.Activo,&c.APIKey,&c.MaxEmpleados,&c.FechaVence)
	render(w, "superadmin/compania_detalle.html", map[string]interface{}{
		"Claims":auth.ClaimsFromCtx(r),"Compania":c,
	})
}

func handlerSAToggleCompania(w http.ResponseWriter, r *http.Request) {
	id, _ := strconv.ParseInt(chi.URLParam(r,"id"), 10, 64)
	db.Get().AdminDB().Exec("UPDATE companias SET activo = CASE WHEN activo=1 THEN 0 ELSE 1 END WHERE id=?", id)
	w.WriteHeader(204)
}

// ── Reportes ──────────────────────────────────────────────────
func handlerReportes(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	render(w, "admin/reportes.html", map[string]interface{}{"Claims":claims})
}

// ── Template helper ───────────────────────────────────────────
func render(w http.ResponseWriter, name string, data interface{}) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := tmpl.ExecuteTemplate(w, name, data); err != nil {
		http.Error(w, "template error: "+err.Error(), 500)
	}
}
