package web

import (
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"strconv"
	"time"

	"desar-server/internal/auth"
	"desar-server/internal/db"
	"desar-server/internal/models"
	"desar-server/internal/pdf"
	"desar-server/internal/ws"

	"github.com/go-chi/chi/v5"
)

var tmpl *template.Template

func Init(t *template.Template) { tmpl = t }

func Router() http.Handler {
	r := chi.NewRouter()

	r.Get("/login",     handlerLoginGet)
	r.Post("/login",    handlerLoginPost)
	r.Get("/logout",    handlerLogout)
	r.Get("/registro",  handlerRegistroGet)
	r.Post("/registro", handlerRegistroPost)

	r.Group(func(r chi.Router) {
		r.Use(auth.MiddlewareWeb)
		r.Get("/",                        handlerDashboard)
		r.Get("/ws",                      handlerWS)
		r.Get("/empleados",               handlerEmpleados)
		r.Delete("/empleados/{id}",       handlerEmpleadoEliminar)
		r.Get("/registros",               handlerRegistros)
		r.Get("/registros/hoy",           handlerRegistrosHoy)
		r.Delete("/registros/{id}",       handlerRegistroEliminar)
		r.Get("/sitios",                  handlerSitios)
		r.Get("/config",                  handlerConfig)
		r.Post("/config",                 handlerConfigSave)
		r.Get("/usuarios",                handlerUsuarios)
		r.Post("/usuarios",               handlerUsuarioCrear)
		r.Post("/usuarios/{id}/editar",   handlerUsuarioEditar)
		r.Delete("/usuarios/{id}",        handlerUsuarioEliminar)
		r.Post("/usuarios/{id}/password", handlerUsuarioCambiarPassword)
		r.Get("/reportes",                handlerReportes)
		r.Get("/reportes/csv",            handlerReportesCSV)
		r.Get("/reportes/excel",          handlerReportesExcel)
		r.Get("/reportes/{tipo}",         handlerReporteTipo)
		r.Get("/pdf/nomina",              handlerPDFNomina)
		r.Get("/pdf/gafetes",             handlerPDFGafetes)
		r.Get("/pdf/vigencias",           handlerPDFVigencias)
	})

	r.Group(func(r chi.Router) {
		r.Use(auth.MiddlewareWeb)
		r.Use(auth.RequierePermiso("companias.ver"))
		r.Get("/sa/companias",                           handlerSACompanias)
		r.Post("/sa/companias",                          handlerSACrearCompania)
		r.Get("/sa/companias/{id}",                      handlerSACompaniaDetalle)
		r.Post("/sa/companias/{id}/editar",              handlerSAEditarCompania)
		r.Put("/sa/companias/{id}/toggle",               handlerSAToggleCompania)
		r.Delete("/sa/companias/{id}",                   handlerSAEliminarCompania)
		r.Get("/sa/companias/{id}/empleados",            handlerSAEmpleadosCompania)
		r.Get("/sa/companias/{id}/registros",            handlerSARegistrosCompania)
		r.Get("/sa/companias/{id}/usuarios",             handlerSAUsuariosCompania)
		r.Post("/sa/companias/{id}/usuarios",            handlerSACrearUsuarioCompania)
		r.Delete("/sa/companias/{id}/usuarios/{uid}",    handlerSAEliminarUsuarioCompania)
		r.Delete("/sa/registros/{id}",                   handlerSAEliminarRegistro)
		r.Delete("/sa/empleados/{id}",                   handlerSAEliminarEmpleado)
	})

	return r
}

// shorthand
func q(s string) string { return db.Q(s) }

// ── Login ─────────────────────────────────────────────────────
func handlerLoginGet(w http.ResponseWriter, r *http.Request) {
	render(w, "auth/login.html", map[string]interface{}{"Error": r.URL.Query().Get("e")})
}

func handlerLoginPost(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	email    := r.FormValue("email")
	password := r.FormValue("password")
	adminDB  := db.Get().AdminDB()
	var u models.Usuario
	var pwHash string
	err := adminDB.QueryRow(q(`SELECT id,compania_id,nombre,email,password_hash,rol,activo
		FROM usuarios WHERE email=$1 AND activo=1`), email).
		Scan(&u.ID, &u.CompaniaID, &u.Nombre, &u.Email, &pwHash, &u.Rol, &u.Activo)
	if err != nil || !auth.VerificarPassword(pwHash, password) {
		http.Redirect(w, r, "/desar/login?e=Credenciales+incorrectas", http.StatusFound); return
	}
	token, err := auth.GenerarToken(&u)
	if err != nil { http.Redirect(w, r, "/desar/login?e=Error+interno", http.StatusFound); return }
	adminDB.Exec(q("UPDATE usuarios SET ultimo_login=$1 WHERE id=$2"), time.Now().Format(time.RFC3339), u.ID)
	db.Get().Audit(u.CompaniaID, u.ID, "login", "usuarios", u.ID, "login exitoso", r.RemoteAddr)
	auth.SetCookie(w, token, r)
	http.Redirect(w, r, "/desar/", http.StatusFound)
}

func handlerLogout(w http.ResponseWriter, r *http.Request) {
	auth.ClearCookie(w)
	http.Redirect(w, r, "/desar/login", http.StatusFound)
}

// ── Auto-registro ─────────────────────────────────────────────
func handlerRegistroGet(w http.ResponseWriter, r *http.Request) {
	render(w, "auth/registro.html", map[string]interface{}{"Error": r.URL.Query().Get("e")})
}

func handlerRegistroPost(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	nombre    := r.FormValue("nombre_compania")
	nombreAdm := r.FormValue("nombre_admin")
	email     := r.FormValue("email")
	password  := r.FormValue("password")
	password2 := r.FormValue("password2")
	telefono  := r.FormValue("telefono")
	redir     := func(e string) { http.Redirect(w, r, "/desar/registro?e="+e, http.StatusFound) }
	if nombre == "" || nombreAdm == "" || email == "" || password == "" { redir("Todos+los+campos+son+requeridos"); return }
	if password != password2 { redir("Las+contraseñas+no+coinciden"); return }
	if len(password) < 8 { redir("La+contraseña+debe+tener+al+menos+8+caracteres"); return }
	adminDB := db.Get().AdminDB()
	var n int
	adminDB.QueryRow(q("SELECT COUNT(*) FROM usuarios WHERE email=$1"), email).Scan(&n)
	if n > 0 { redir("El+email+ya+está+registrado"); return }
	apiKey := auth.GenerarAPIKey()
	dbPath := db.Get().NewCompanyDBPath(apiKey)
	res, err := adminDB.Exec(q(`INSERT INTO companias(nombre,email,telefono,api_key,plan,max_empleados,max_dispositivos,activo,db_path)
		VALUES($1,$2,$3,$4,'basico',25,3,1,$5)`), nombre, email, telefono, apiKey, dbPath)
	if err != nil { redir("Error+al+crear+compañía"); return }
	compID, _ := res.LastInsertId()
	hash, _ := auth.HashPassword(password)
	adminDB.Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,'admin')"), compID, nombreAdm, email, hash)
	db.Get().CompanyDB(compID)
	db.Get().Audit(compID, 0, "registro", "companias", compID, "auto-registro", r.RemoteAddr)
	http.Redirect(w, r, "/desar/login?e=Compañía+creada.+Inicia+sesión", http.StatusFound)
}

// ── Dashboard ─────────────────────────────────────────────────
func handlerDashboard(w http.ResponseWriter, r *http.Request) {
	claims  := auth.ClaimsFromCtx(r)
	compDB, err := db.Get().CompanyDB(claims.CompaniaID)
	if err != nil { http.Error(w, "BD error", 500); return }
	hoy := time.Now().Format("2006-01-02")
	var totalEmp, presentes, salidas, regHoy int
	compDB.QueryRow(q("SELECT COUNT(*) FROM empleados WHERE activo=1")).Scan(&totalEmp)
	compDB.QueryRow(q("SELECT COUNT(*) FROM registros WHERE tipo='entrada' AND timestamp LIKE $1"), hoy+"%").Scan(&presentes)
	compDB.QueryRow(q("SELECT COUNT(*) FROM registros WHERE tipo='salida' AND timestamp LIKE $1"), hoy+"%").Scan(&salidas)
	compDB.QueryRow(q("SELECT COUNT(*) FROM registros WHERE timestamp LIKE $1"), hoy+"%").Scan(&regHoy)
	rows, _ := compDB.Query(q(`SELECT codigo_empleado,nombre_empleado,tipo,timestamp,sitio_trabajo,metodo
		FROM registros WHERE timestamp LIKE $1 ORDER BY timestamp DESC LIMIT 20`), hoy+"%")
	var registros []map[string]interface{}
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var cod, nom, tipo, ts, sitio, metodo string
			rows.Scan(&cod, &nom, &tipo, &ts, &sitio, &metodo)
			registros = append(registros, map[string]interface{}{
				"CodigoEmpleado": cod, "NombreEmpleado": nom, "Tipo": tipo,
				"Timestamp": ts, "SitioTrabajo": sitio, "Metodo": metodo,
			})
		}
	}
	render(w, "admin/dashboard.html", map[string]interface{}{
		"Claims": claims, "TotalEmp": totalEmp, "Presentes": presentes,
		"Salidas": salidas, "RegHoy": regHoy, "Registros": registros, "Hoy": hoy,
	})
}

func handlerWS(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	ws.Handler(w, r, claims.CompaniaID)
}

// ── Empleados ─────────────────────────────────────────────────
func handlerEmpleados(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	busq := r.URL.Query().Get("q")
	baseQ := "SELECT id,codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),activo,COALESCE(fecha_vencimiento,'') FROM empleados WHERE 1=1"
	args := []interface{}{}
	if busq != "" {
		baseQ += " AND (nombre LIKE $1 OR codigo_empleado LIKE $2)"
		args = append(args, "%"+busq+"%", "%"+busq+"%")
	}
	baseQ += " ORDER BY nombre ASC"
	rows, _ := compDB.Query(q(baseQ), args...)
	var empleados []map[string]interface{}
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var cod, nom, puesto, sitio, fv string; var activo int
			rows.Scan(&id, &cod, &nom, &puesto, &sitio, &activo, &fv)
			empleados = append(empleados, map[string]interface{}{
				"ID": cod, "Nombre": nom, "Puesto": puesto, "SitioTrabajo": sitio,
				"Activo": activo == 1, "FechaVencimiento": fv, "DBID": id,
			})
		}
	}
	render(w, "admin/empleados.html", map[string]interface{}{"Claims": claims, "Empleados": empleados, "Busq": busq})
}

func handlerEmpleadoEliminar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.eliminar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	compDB.Exec(q("DELETE FROM empleados WHERE id=$1"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "eliminar", "empleados", id, "", r.RemoteAddr)
	w.WriteHeader(200)
}

// ── Registros ─────────────────────────────────────────────────
func handlerRegistros(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta"); emp := r.URL.Query().Get("emp")
	if desde == "" { desde = time.Now().Format("2006-01-02") }
	if hasta == "" { hasta = desde }
	baseQ := "SELECT id,codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,''),metodo FROM registros WHERE timestamp >= $1 AND timestamp <= $2"
	args := []interface{}{desde + "T00:00:00", hasta + "T23:59:59"}
	if emp != "" {
		baseQ += " AND (codigo_empleado LIKE $3 OR nombre_empleado LIKE $4)"
		args = append(args, "%"+emp+"%", "%"+emp+"%")
	}
	baseQ += " ORDER BY timestamp DESC LIMIT 500"
	rows, _ := compDB.Query(q(baseQ), args...)
	var registros []map[string]interface{}
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var cod, nom, tipo, ts, sitio, metodo string
			rows.Scan(&id, &cod, &nom, &tipo, &ts, &sitio, &metodo)
			registros = append(registros, map[string]interface{}{
				"ID": id, "CodigoEmpleado": cod, "NombreEmpleado": nom,
				"Tipo": tipo, "Timestamp": ts, "SitioTrabajo": sitio, "Metodo": metodo,
			})
		}
	}
	render(w, "admin/registros.html", map[string]interface{}{
		"Claims": claims, "Registros": registros, "Desde": desde, "Hasta": hasta, "Emp": emp,
	})
}

func handlerRegistrosHoy(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	hoy := time.Now().Format("2006-01-02")
	rows, _ := compDB.Query(q("SELECT codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,'') FROM registros WHERE timestamp LIKE $1 ORDER BY timestamp DESC"), hoy+"%")
	var data []map[string]string
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var cod, nom, tipo, ts, sitio string
			rows.Scan(&cod, &nom, &tipo, &ts, &sitio)
			data = append(data, map[string]string{"cod": cod, "nom": nom, "tipo": tipo, "ts": ts, "sitio": sitio})
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

func handlerRegistroEliminar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "registros.eliminar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	compDB.Exec(q("DELETE FROM registros WHERE id=$1"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "eliminar", "registros", id, "", r.RemoteAddr)
	w.WriteHeader(200)
}

// ── Sitios ────────────────────────────────────────────────────
func handlerSitios(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	rows, _ := compDB.Query("SELECT id,nombre,COALESCE(descripcion,''),activo FROM sitios ORDER BY nombre")
	var sitios []map[string]interface{}
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var nom, desc string; var act int
			rows.Scan(&id, &nom, &desc, &act)
			sitios = append(sitios, map[string]interface{}{"ID": id, "Nombre": nom, "Descripcion": desc, "Activo": act == 1})
		}
	}
	render(w, "admin/sitios.html", map[string]interface{}{"Claims": claims, "Sitios": sitios})
}

// ── Config ────────────────────────────────────────────────────
func handlerConfig(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "config.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var nom, he, hs string; var tol int
	compDB.QueryRow("SELECT nombre_compania,hora_entrada_default,hora_salida_default,tolerancia_minutos FROM configuracion WHERE id=1").Scan(&nom, &he, &hs, &tol)
	render(w, "admin/config.html", map[string]interface{}{"Claims": claims, "NombreCompania": nom, "HoraEntrada": he, "HoraSalida": hs, "Tolerancia": tol})
}

func handlerConfigSave(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "config.editar") { http.Error(w, "403", 403); return }
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	nom := r.FormValue("nombre_compania"); he := r.FormValue("hora_entrada"); hs := r.FormValue("hora_salida")
	tol, _ := strconv.Atoi(r.FormValue("tolerancia"))
	compDB.Exec(q(`INSERT INTO configuracion(id,nombre_compania,hora_entrada_default,hora_salida_default,tolerancia_minutos)
		VALUES(1,$1,$2,$3,$4) ON CONFLICT(id) DO UPDATE SET nombre_compania=excluded.nombre_compania,
		hora_entrada_default=excluded.hora_entrada_default,hora_salida_default=excluded.hora_salida_default,
		tolerancia_minutos=excluded.tolerancia_minutos`), nom, he, hs, tol)
	http.Redirect(w, r, "/desar/config?ok=1", http.StatusFound)
}

// ── Usuarios ──────────────────────────────────────────────────
func handlerUsuarios(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.ver") { http.Error(w, "403", 403); return }
	rows, _ := db.Get().AdminDB().Query(q("SELECT id,nombre,email,rol,activo,COALESCE(ultimo_login,'') FROM usuarios WHERE compania_id=$1 ORDER BY nombre"), claims.CompaniaID)
	var usuarios []map[string]interface{}
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var nom, email, rol, ul string; var act int
			rows.Scan(&id, &nom, &email, &rol, &act, &ul)
			usuarios = append(usuarios, map[string]interface{}{"ID": id, "Nombre": nom, "Email": email, "Rol": rol, "Activo": act == 1, "UltimoLogin": ul})
		}
	}
	render(w, "admin/usuarios.html", map[string]interface{}{
		"Claims": claims, "Usuarios": usuarios,
		"Roles": auth.RolesDisponibles(claims.Rol), "Ok": r.URL.Query().Get("ok") == "1",
	})
}

func handlerUsuarioCrear(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.crear") { http.Error(w, "403", 403); return }
	r.ParseForm()
	nom   := r.FormValue("nombre"); email := r.FormValue("email")
	pw    := r.FormValue("password"); rol  := r.FormValue("rol")
	puedeAsignar := false
	for _, rr := range auth.RolesDisponibles(claims.Rol) { if rr == rol { puedeAsignar = true; break } }
	if !puedeAsignar { http.Error(w, "403 rol no permitido", 403); return }
	if nom == "" || email == "" || pw == "" { http.Error(w, "campos requeridos", 400); return }
	hash, _ := auth.HashPassword(pw)
	db.Get().AdminDB().Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,$5)"), claims.CompaniaID, nom, email, hash, rol)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear_usuario", "usuarios", 0, email, r.RemoteAddr)
	http.Redirect(w, r, "/desar/usuarios?ok=1", http.StatusFound)
}

func handlerUsuarioEditar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	nom := r.FormValue("nombre"); rol := r.FormValue("rol")
	puedeAsignar := false
	for _, rr := range auth.RolesDisponibles(claims.Rol) { if rr == rol { puedeAsignar = true; break } }
	if !puedeAsignar { http.Error(w, "403 rol no permitido", 403); return }
	db.Get().AdminDB().Exec(q("UPDATE usuarios SET nombre=$1, rol=$2 WHERE id=$3 AND compania_id=$4"), nom, rol, id, claims.CompaniaID)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "editar_usuario", "usuarios", id, rol, r.RemoteAddr)
	http.Redirect(w, r, "/desar/usuarios?ok=1", http.StatusFound)
}

func handlerUsuarioEliminar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.eliminar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if id == claims.UserID { http.Error(w, "no puedes eliminar tu propia cuenta", 400); return }
	db.Get().AdminDB().Exec(q("UPDATE usuarios SET activo=0 WHERE id=$1 AND compania_id=$2"), id, claims.CompaniaID)
	w.WriteHeader(200)
}

func handlerUsuarioCambiarPassword(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if id != claims.UserID && !auth.Puede(claims.Rol, "usuarios.editar") { http.Error(w, "403", 403); return }
	r.ParseForm()
	pw := r.FormValue("password")
	if len(pw) < 8 { http.Error(w, "mínimo 8 caracteres", 400); return }
	hash, _ := auth.HashPassword(pw)
	db.Get().AdminDB().Exec(q("UPDATE usuarios SET password_hash=$1 WHERE id=$2"), hash, id)
	w.WriteHeader(200)
}

// ── Reportes ──────────────────────────────────────────────────
func handlerReportes(w http.ResponseWriter, r *http.Request) {
	render(w, "admin/reportes.html", map[string]interface{}{"Claims": auth.ClaimsFromCtx(r)})
}

func handlerReportesCSV(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "reportes.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().AddDate(0, 0, -30).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	rows, err := compDB.Query(q(`SELECT codigo_empleado,nombre_empleado,tipo,timestamp,
		COALESCE(sitio_trabajo,''),metodo,COALESCE(CAST(gps_lat AS TEXT),''),
		COALESCE(CAST(gps_lon AS TEXT),''),COALESCE(notas,'')
		FROM registros WHERE timestamp >= $1 AND timestamp <= $2 ORDER BY timestamp DESC`),
		desde+"T00:00:00", hasta+"T23:59:59")
	if err != nil { http.Error(w, "Error BD", 500); return }
	defer rows.Close()
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	w.Header().Set("Content-Disposition", `attachment; filename="registros_`+desde+`_`+hasta+`.csv"`)
	w.Write([]byte("\xEF\xBB\xBF"))
	w.Write([]byte("Código,Nombre,Tipo,Timestamp,Sitio,Método,GPS_Lat,GPS_Lon,Notas\n"))
	for rows.Next() {
		var cod, nom, tipo, ts, sitio, metodo, lat, lon, notas string
		rows.Scan(&cod, &nom, &tipo, &ts, &sitio, &metodo, &lat, &lon, &notas)
		fmt.Fprintf(w, "%s,%s,%s,%s,%s,%s,%s,%s,%q\n", cod, nom, tipo, ts, sitio, metodo, lat, lon, notas)
	}
}

func handlerReportesExcel(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "reportes.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta"); tipo := r.URL.Query().Get("tipo")
	if desde == "" { desde = time.Now().AddDate(0, 0, -30).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	if tipo == "" { tipo = "asistencias" }
	w.Header().Set("Content-Type", "application/vnd.ms-excel; charset=utf-8")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="%s_%s_%s.xls"`, tipo, desde, hasta))
	w.Write([]byte("\xEF\xBB\xBF"))
	switch tipo {
	case "empleados":
		w.Write([]byte("Código\tNombre\tPuesto\tSitio\tIMSS\tFecha Alta\tFecha Venc\tActivo\n"))
		rows, _ := compDB.Query("SELECT codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),COALESCE(seguro_social,''),COALESCE(fecha_alta,''),COALESCE(fecha_vencimiento,''),activo FROM empleados ORDER BY nombre")
		if rows != nil { defer rows.Close(); for rows.Next() {
			var cod, nom, puesto, sitio, imss, fa, fv string; var act int
			rows.Scan(&cod, &nom, &puesto, &sitio, &imss, &fa, &fv, &act)
			estado := "Activo"; if act == 0 { estado = "Baja" }
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", cod, nom, puesto, sitio, imss, fa, fv, estado)
		}}
	case "tardanzas":
		hora := r.URL.Query().Get("hora_entrada"); if hora == "" { hora = "08:00" }
		w.Write([]byte("Código\tNombre\tFecha\tHora Entrada\tTardanza\n"))
		rows, _ := compDB.Query(q(`SELECT codigo_empleado,nombre_empleado,date(timestamp),strftime('%H:%M',timestamp)
			FROM registros WHERE tipo='entrada' AND timestamp >= $1 AND timestamp <= $2
			AND strftime('%H:%M',timestamp) > $3 ORDER BY timestamp`), desde+"T00:00:00", hasta+"T23:59:59", hora)
		if rows != nil { defer rows.Close(); for rows.Next() {
			var cod, nom, fecha, horaEnt string; rows.Scan(&cod, &nom, &fecha, &horaEnt)
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\tSí\n", cod, nom, fecha, horaEnt)
		}}
	default:
		w.Write([]byte("Código\tNombre\tFecha\tHora\tTipo\tMétodo\tSitio\n"))
		rows, _ := compDB.Query(q(`SELECT codigo_empleado,nombre_empleado,date(timestamp),strftime('%H:%M:%S',timestamp),tipo,metodo,COALESCE(sitio_trabajo,'')
			FROM registros WHERE timestamp >= $1 AND timestamp <= $2 ORDER BY timestamp DESC`), desde+"T00:00:00", hasta+"T23:59:59")
		if rows != nil { defer rows.Close(); for rows.Next() {
			var cod, nom, fecha, hora, tipo2, metodo, sitio string
			rows.Scan(&cod, &nom, &fecha, &hora, &tipo2, &metodo, &sitio)
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", cod, nom, fecha, hora, tipo2, metodo, sitio)
		}}
	}
}

func handlerReporteTipo(w http.ResponseWriter, r *http.Request) {
	render(w, "admin/reporte_tipo.html", map[string]interface{}{"Claims": auth.ClaimsFromCtx(r), "Tipo": chi.URLParam(r, "tipo")})
}

// ── PDF ───────────────────────────────────────────────────────
func handlerPDFNomina(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "pdf.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().AddDate(0, 0, -14).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	var compNom string
	compDB.QueryRow("SELECT COALESCE(nombre_compania,'DESAR') FROM configuracion WHERE id=1").Scan(&compNom)
	data, err := pdf.GenerarNomina(compDB, compNom, desde+"T00:00:00", hasta+"T23:59:59")
	if err != nil { http.Error(w, "Error PDF: "+err.Error(), 500); return }
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="nomina_%s_%s.pdf"`, desde, hasta))
	w.Write(data)
}

func handlerPDFGafetes(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "pdf.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var compNom string
	compDB.QueryRow("SELECT COALESCE(nombre_compania,'DESAR') FROM configuracion WHERE id=1").Scan(&compNom)
	rows, _ := compDB.Query("SELECT codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,'') FROM empleados WHERE activo=1 ORDER BY nombre")
	var lista []pdf.EmpleadoGafete
	if rows != nil { defer rows.Close(); for rows.Next() {
		var e pdf.EmpleadoGafete
		rows.Scan(&e.Codigo, &e.Nombre, &e.Puesto, &e.Sitio)
		e.QRData = e.Codigo; lista = append(lista, e)
	}}
	data, err := pdf.GenerarCatalogoGafetes(lista, compNom)
	if err != nil { http.Error(w, "Error PDF: "+err.Error(), 500); return }
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", `attachment; filename="gafetes.pdf"`)
	w.Write(data)
}

func handlerPDFVigencias(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "pdf.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var compNom string
	compDB.QueryRow("SELECT COALESCE(nombre_compania,'DESAR') FROM configuracion WHERE id=1").Scan(&compNom)
	data, err := pdf.GenerarReporteVigencias(compDB, compNom)
	if err != nil { http.Error(w, "Error PDF: "+err.Error(), 500); return }
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", `attachment; filename="vigencias.pdf"`)
	w.Write(data)
}

// ── Superadmin ────────────────────────────────────────────────
func handlerSACompanias(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	rows, _ := db.Get().AdminDB().Query("SELECT id,nombre,plan,activo,api_key,COALESCE(fecha_vence,'') FROM companias ORDER BY id")
	var companias []map[string]interface{}
	if rows != nil { defer rows.Close(); for rows.Next() {
		var id int64; var nom, plan, apikey, fv string; var act int
		rows.Scan(&id, &nom, &plan, &act, &apikey, &fv)
		companias = append(companias, map[string]interface{}{"ID": id, "Nombre": nom, "Plan": plan, "Activo": act == 1, "APIKey": apikey, "FechaVence": fv})
	}}
	render(w, "superadmin/companias.html", map[string]interface{}{"Claims": claims, "Companias": companias})
}

func handlerSACrearCompania(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	claims := auth.ClaimsFromCtx(r)
	apiKey := auth.GenerarAPIKey()
	dbPath := db.Get().NewCompanyDBPath(apiKey)
	res, err := db.Get().AdminDB().Exec(q("INSERT INTO companias(nombre,email,api_key,plan,activo,fecha_vence,db_path) VALUES($1,$2,$3,$4,1,$5,$6)"),
		r.FormValue("nombre"), r.FormValue("email"), apiKey, r.FormValue("plan"), r.FormValue("fecha_vence"), dbPath)
	if err != nil { http.Error(w, "Error: "+err.Error(), 500); return }
	compID, _ := res.LastInsertId()
	db.Get().CompanyDB(compID)
	if em := r.FormValue("email"); em != "" && r.FormValue("password") != "" {
		hash, _ := auth.HashPassword(r.FormValue("password"))
		db.Get().AdminDB().Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,'admin')"), compID, r.FormValue("nombre"), em, hash)
	}
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear", "companias", compID, r.FormValue("nombre"), r.RemoteAddr)
	http.Redirect(w, r, "/desar/sa/companias", http.StatusFound)
}

func handlerSAEditarCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	maxEmp, _ := strconv.Atoi(r.FormValue("max_empleados")); if maxEmp == 0 { maxEmp = 25 }
	db.Get().AdminDB().Exec(q("UPDATE companias SET nombre=$1, plan=$2, email=$3, fecha_vence=$4, max_empleados=$5 WHERE id=$6"),
		r.FormValue("nombre"), r.FormValue("plan"), r.FormValue("email"), r.FormValue("fecha_vence"), maxEmp, id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "editar", "companias", id, r.FormValue("nombre"), r.RemoteAddr)
	http.Redirect(w, r, fmt.Sprintf("/desar/sa/companias/%d", id), http.StatusFound)
}

func handlerSACompaniaDetalle(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	var c struct{ ID int64; Nombre, Plan, APIKey, Email, FechaVence string; Activo, MaxEmp int }
	db.Get().AdminDB().QueryRow(q("SELECT id,nombre,plan,api_key,COALESCE(email,''),activo,COALESCE(fecha_vence,''),max_empleados FROM companias WHERE id=$1"), id).
		Scan(&c.ID, &c.Nombre, &c.Plan, &c.APIKey, &c.Email, &c.Activo, &c.FechaVence, &c.MaxEmp)
	compDB, _ := db.Get().CompanyDB(id)
	var totalEmp, totalReg int
	if compDB != nil { compDB.QueryRow("SELECT COUNT(*) FROM empleados").Scan(&totalEmp); compDB.QueryRow("SELECT COUNT(*) FROM registros").Scan(&totalReg) }
	render(w, "superadmin/compania_detalle.html", map[string]interface{}{
		"Claims": claims, "C": c, "TotalEmp": totalEmp, "TotalReg": totalReg,
		"Planes": []string{"basico", "estandar", "enterprise"},
	})
}

func handlerSAToggleCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	var act int
	db.Get().AdminDB().QueryRow(q("SELECT activo FROM companias WHERE id=$1"), id).Scan(&act)
	nuevo := 1; if act == 1 { nuevo = 0 }
	db.Get().AdminDB().Exec(q("UPDATE companias SET activo=$1 WHERE id=$2"), nuevo, id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "toggle", "companias", id, fmt.Sprintf("activo=%d", nuevo), r.RemoteAddr)
	w.WriteHeader(200)
}

func handlerSAEliminarCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	db.Get().AdminDB().Exec(q("UPDATE companias SET activo=0 WHERE id=$1"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "eliminar", "companias", id, "", r.RemoteAddr)
	w.WriteHeader(200)
}

func handlerSAEmpleadosCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(id)
	var nombre string
	db.Get().AdminDB().QueryRow(q("SELECT nombre FROM companias WHERE id=$1"), id).Scan(&nombre)
	rows, _ := compDB.Query("SELECT id,codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),activo FROM empleados ORDER BY nombre")
	var lista []map[string]interface{}
	if rows != nil { defer rows.Close(); for rows.Next() {
		var dbid int64; var cod, nom, puesto, sitio string; var act int
		rows.Scan(&dbid, &cod, &nom, &puesto, &sitio, &act)
		lista = append(lista, map[string]interface{}{"DBID": dbid, "ID": cod, "Nombre": nom, "Puesto": puesto, "SitioTrabajo": sitio, "Activo": act == 1})
	}}
	render(w, "superadmin/compania_empleados.html", map[string]interface{}{"Claims": claims, "Empleados": lista, "CompaniaID": id, "CompaniaNombre": nombre})
}

func handlerSARegistrosCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(id)
	var nombre string
	db.Get().AdminDB().QueryRow(q("SELECT nombre FROM companias WHERE id=$1"), id).Scan(&nombre)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().Format("2006-01-02") }; if hasta == "" { hasta = desde }
	rows, _ := compDB.Query(q(`SELECT id,codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,''),metodo
		FROM registros WHERE timestamp >= $1 AND timestamp <= $2 ORDER BY timestamp DESC LIMIT 500`), desde+"T00:00:00", hasta+"T23:59:59")
	var lista []map[string]interface{}
	if rows != nil { defer rows.Close(); for rows.Next() {
		var dbid int64; var cod, nom, tipo, ts, sitio, metodo string
		rows.Scan(&dbid, &cod, &nom, &tipo, &ts, &sitio, &metodo)
		lista = append(lista, map[string]interface{}{"ID": dbid, "CodigoEmpleado": cod, "NombreEmpleado": nom, "Tipo": tipo, "Timestamp": ts, "SitioTrabajo": sitio, "Metodo": metodo})
	}}
	render(w, "superadmin/compania_registros.html", map[string]interface{}{"Claims": claims, "Registros": lista, "CompaniaID": id, "CompaniaNombre": nombre, "Desde": desde, "Hasta": hasta})
}

func handlerSAEliminarRegistro(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(r.URL.Query().Get("compania_id"), 10, 64)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if compID == 0 { compID = claims.CompaniaID }
	compDB, _ := db.Get().CompanyDB(compID)
	if compDB != nil { compDB.Exec(q("DELETE FROM registros WHERE id=$1"), id) }
	db.Get().Audit(claims.CompaniaID, claims.UserID, "eliminar", "registros", id, fmt.Sprintf("cia=%d", compID), r.RemoteAddr)
	w.WriteHeader(200)
}

func handlerSAEliminarEmpleado(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(r.URL.Query().Get("compania_id"), 10, 64)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if compID == 0 { compID = claims.CompaniaID }
	compDB, _ := db.Get().CompanyDB(compID)
	if compDB != nil { compDB.Exec(q("DELETE FROM empleados WHERE id=$1"), id) }
	db.Get().Audit(claims.CompaniaID, claims.UserID, "eliminar", "empleados", id, fmt.Sprintf("cia=%d", compID), r.RemoteAddr)
	w.WriteHeader(200)
}

func handlerSAUsuariosCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	var compNom string
	db.Get().AdminDB().QueryRow(q("SELECT nombre FROM companias WHERE id=$1"), compID).Scan(&compNom)
	rows, _ := db.Get().AdminDB().Query(q("SELECT id,nombre,email,rol,activo FROM usuarios WHERE compania_id=$1 ORDER BY nombre"), compID)
	var lista []map[string]interface{}
	if rows != nil { defer rows.Close(); for rows.Next() {
		var id int64; var nom, email, rol string; var act int
		rows.Scan(&id, &nom, &email, &rol, &act)
		lista = append(lista, map[string]interface{}{"ID": id, "Nombre": nom, "Email": email, "Rol": rol, "Activo": act == 1})
	}}
	render(w, "superadmin/compania_usuarios.html", map[string]interface{}{"Claims": claims, "Usuarios": lista, "CompaniaID": compID, "CompaniaNombre": compNom, "Roles": auth.Roles})
}

func handlerSACrearUsuarioCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	nom := r.FormValue("nombre"); email := r.FormValue("email"); pw := r.FormValue("password"); rol := r.FormValue("rol")
	if nom == "" || email == "" || pw == "" { http.Error(w, "campos requeridos", 400); return }
	hash, _ := auth.HashPassword(pw)
	db.Get().AdminDB().Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,$5)"), compID, nom, email, hash, rol)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear_usuario", "usuarios", 0, email, r.RemoteAddr)
	http.Redirect(w, r, fmt.Sprintf("/desar/sa/companias/%d/usuarios", compID), http.StatusFound)
}

func handlerSAEliminarUsuarioCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	uid, _    := strconv.ParseInt(chi.URLParam(r, "uid"), 10, 64)
	db.Get().AdminDB().Exec(q("UPDATE usuarios SET activo=0 WHERE id=$1 AND compania_id=$2"), uid, compID)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "desactivar_usuario", "usuarios", uid, fmt.Sprintf("cia=%d", compID), r.RemoteAddr)
	w.WriteHeader(200)
}

func render(w http.ResponseWriter, name string, data interface{}) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := tmpl.ExecuteTemplate(w, name, data); err != nil {
		http.Error(w, "template error: "+err.Error(), 500)
	}
}
