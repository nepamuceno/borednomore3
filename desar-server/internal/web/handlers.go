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
	"database/sql"
	"desar-server/internal/ws"

	"github.com/go-chi/chi/v5"
)

var tmpl *template.Template

func Init(t *template.Template) { tmpl = t }

func Router() http.Handler {
	r := chi.NewRouter()

	// Públicas
	r.Get("/login",     handlerLoginGet)
	r.Post("/login",    handlerLoginPost)
	r.Get("/logout",    handlerLogout)
	r.Get("/registro",  handlerRegistroGet)
	r.Post("/registro", handlerRegistroPost)

	// Panel — autenticado
	r.Group(func(r chi.Router) {
		r.Use(auth.MiddlewareWeb)

		r.Get("/",    handlerDashboard)
		r.Get("/ws",  handlerWS)

		// Empleados
		r.Get("/empleados",                handlerEmpleados)
		r.Get("/empleados/nuevo",          handlerEmpleadoNuevoGet)
		r.Post("/empleados/nuevo",         handlerEmpleadoNuevoPost)
		r.Get("/empleados/{id}/editar",    handlerEmpleadoEditarGet)
		r.Post("/empleados/{id}/editar",   handlerEmpleadoEditarPost)
		r.Post("/empleados/{id}/baja",     handlerEmpleadoBaja)
		r.Delete("/empleados/{id}",        handlerEmpleadoEliminar)

		// Registros
		r.Get("/registros",                handlerRegistros)
		r.Get("/registros/hoy",            handlerRegistrosHoy)
		r.Get("/registros/nuevo",          handlerRegistroNuevoGet)
		r.Post("/registros/nuevo",         handlerRegistroNuevoPost)
		r.Delete("/registros/{id}",        handlerRegistroEliminar)

		// Sitios
		r.Get("/sitios",                   handlerSitios)
		r.Get("/sitios/nuevo",             handlerSitioNuevoGet)
		r.Post("/sitios/nuevo",            handlerSitioNuevoPost)
		r.Get("/sitios/{id}/editar",       handlerSitioEditarGet)
		r.Post("/sitios/{id}/editar",      handlerSitioEditarPost)
		r.Delete("/sitios/{id}",           handlerSitioEliminar)

		// Reportes y PDF
		r.Get("/reportes",                 handlerReportes)
		r.Get("/reportes/csv",             handlerReportesCSV)
		r.Get("/reportes/excel",           handlerReportesExcel)
		r.Get("/reportes/{tipo}",          handlerReporteTipo)
		r.Get("/pdf/nomina",               handlerPDFNomina)
		r.Get("/pdf/gafetes",              handlerPDFGafetes)
		r.Get("/pdf/vigencias",            handlerPDFVigencias)
		r.Get("/pdf/registros",            handlerPDFRegistros)
		r.Get("/pdf/tardanzas",            handlerPDFTardanzas)
		r.Get("/pdf/catalogo-qr",          handlerPDFCatalogoQR)
		r.Get("/reportes/excel/tardanzas", handlerExcelTardanzas)
		r.Get("/reportes/excel/registros", handlerExcelRegistros)
		r.Get("/reportes/excel/catalogo",  handlerExcelCatalogo)

		// Config
		r.Get("/config",                   handlerConfig)
		r.Post("/config",                  handlerConfigSave)

		// Usuarios
		r.Get("/usuarios",                 handlerUsuarios)
		r.Post("/usuarios",                handlerUsuarioCrear)
		r.Post("/usuarios/{id}/editar",    handlerUsuarioEditar)
		r.Delete("/usuarios/{id}",         handlerUsuarioEliminar)
		r.Post("/usuarios/{id}/password",  handlerUsuarioCambiarPassword)
	})

	// Superadmin
	r.Group(func(r chi.Router) {
		r.Use(auth.MiddlewareWeb)
		r.Use(auth.RequierePermiso("companias.ver"))
		r.Get("/sa/companias",                        handlerSACompanias)
		r.Post("/sa/companias",                       handlerSACrearCompania)
		r.Get("/sa/companias/{id}",                   handlerSACompaniaDetalle)
		r.Post("/sa/companias/{id}/editar",           handlerSAEditarCompania)
		r.Put("/sa/companias/{id}/toggle",            handlerSAToggleCompania)
		r.Delete("/sa/companias/{id}",                handlerSAEliminarCompania)
		r.Get("/sa/companias/{id}/empleados",         handlerSAEmpleadosCompania)
		r.Get("/sa/companias/{id}/registros",         handlerSARegistrosCompania)
		r.Get("/sa/companias/{id}/usuarios",          handlerSAUsuariosCompania)
		r.Post("/sa/companias/{id}/usuarios",         handlerSACrearUsuarioCompania)
		r.Delete("/sa/companias/{id}/usuarios/{uid}", handlerSAEliminarUsuarioCompania)
		r.Delete("/sa/registros/{id}",                handlerSAEliminarRegistro)
		r.Delete("/sa/empleados/{id}",                handlerSAEliminarEmpleado)
	})

	return r
}

func q(s string) string { return db.Q(s) }

// ── Login / Logout / Registro ─────────────────────────────────
func handlerLoginGet(w http.ResponseWriter, r *http.Request) {
	render(w, "auth/login.html", M{"Error": r.URL.Query().Get("e")})
}
func handlerLoginPost(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	email, password := r.FormValue("email"), r.FormValue("password")
	adminDB := db.Get().AdminDB()
	var u models.Usuario
	var pwHash string
	err := adminDB.QueryRow(q("SELECT id,compania_id,nombre,email,password_hash,rol,activo FROM usuarios WHERE email=$1 AND activo=1"), email).
		Scan(&u.ID, &u.CompaniaID, &u.Nombre, &u.Email, &pwHash, &u.Rol, &u.Activo)
	if err != nil || !auth.VerificarPassword(pwHash, password) {
		http.Redirect(w, r, "/desar/login?e=Credenciales+incorrectas", 302); return
	}
	token, _ := auth.GenerarToken(&u)
	adminDB.Exec(q("UPDATE usuarios SET ultimo_login=$1 WHERE id=$2"), time.Now().Format(time.RFC3339), u.ID)
	db.Get().Audit(u.CompaniaID, u.ID, "login", "usuarios", u.ID, "", r.RemoteAddr)
	auth.SetCookie(w, token, r)
	http.Redirect(w, r, "/desar/", 302)
}
func handlerLogout(w http.ResponseWriter, r *http.Request) {
	auth.ClearCookie(w)
	http.Redirect(w, r, "/desar/login", 302)
}
func handlerRegistroGet(w http.ResponseWriter, r *http.Request) {
	render(w, "auth/registro.html", M{"Error": r.URL.Query().Get("e")})
}
func handlerRegistroPost(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	nombre, nombreAdm, email, pw, pw2, tel :=
		r.FormValue("nombre_compania"), r.FormValue("nombre_admin"),
		r.FormValue("email"), r.FormValue("password"), r.FormValue("password2"),
		r.FormValue("telefono")
	redir := func(e string) { http.Redirect(w, r, "/desar/registro?e="+e, 302) }
	if nombre == "" || nombreAdm == "" || email == "" || pw == "" { redir("Campos+requeridos"); return }
	if pw != pw2 { redir("Contraseñas+no+coinciden"); return }
	if len(pw) < 8 { redir("Contraseña+mínimo+8+caracteres"); return }
	adminDB := db.Get().AdminDB()
	var n int
	adminDB.QueryRow(q("SELECT COUNT(*) FROM usuarios WHERE email=$1"), email).Scan(&n)
	if n > 0 { redir("Email+ya+registrado"); return }
	apiKey := auth.GenerarAPIKey()
	dbPath := db.Get().NewCompanyDBPath(apiKey)
	res, err := adminDB.Exec(q("INSERT INTO companias(nombre,email,telefono,api_key,plan,max_empleados,max_dispositivos,activo,db_path) VALUES($1,$2,$3,$4,'basico',25,3,1,$5)"),
		nombre, email, tel, apiKey, dbPath)
	if err != nil { redir("Error+al+crear+compañía"); return }
	compID, _ := res.LastInsertId()
	hash, _ := auth.HashPassword(pw)
	adminDB.Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,'admin')"), compID, nombreAdm, email, hash)
	db.Get().CompanyDB(compID)
	db.Get().Audit(compID, 0, "registro", "companias", compID, "auto-registro", r.RemoteAddr)
	http.Redirect(w, r, "/desar/login?e=Compañía+creada.+Inicia+sesión", 302)
}

// ── Dashboard ─────────────────────────────────────────────────
func handlerDashboard(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, err := db.Get().CompanyDB(claims.CompaniaID)
	if err != nil { http.Error(w, "BD error", 500); return }
	hoy := time.Now().Format("2006-01-02")
	var totalEmp, presentes, salidas, regHoy int
	compDB.QueryRow("SELECT COUNT(*) FROM empleados WHERE activo=1").Scan(&totalEmp)
	compDB.QueryRow(q("SELECT COUNT(*) FROM registros WHERE tipo='entrada' AND timestamp LIKE $1"), hoy+"%").Scan(&presentes)
	compDB.QueryRow(q("SELECT COUNT(*) FROM registros WHERE tipo='salida'  AND timestamp LIKE $1"), hoy+"%").Scan(&salidas)
	compDB.QueryRow(q("SELECT COUNT(*) FROM registros WHERE timestamp LIKE $1"), hoy+"%").Scan(&regHoy)
	rows, _ := compDB.Query(q("SELECT codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,''),metodo FROM registros WHERE timestamp LIKE $1 ORDER BY timestamp DESC LIMIT 20"), hoy+"%")
	var registros []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var cod, nom, tipo, ts, sitio, metodo string
			rows.Scan(&cod, &nom, &tipo, &ts, &sitio, &metodo)
			registros = append(registros, M{"CodigoEmpleado": cod, "NombreEmpleado": nom, "Tipo": tipo, "Timestamp": ts, "SitioTrabajo": sitio, "Metodo": metodo})
		}
	}
	render(w, "admin/dashboard.html", M{"Claims": claims, "TotalEmp": totalEmp, "Presentes": presentes, "Salidas": salidas, "RegHoy": regHoy, "Registros": registros, "Hoy": hoy})
}
func handlerWS(w http.ResponseWriter, r *http.Request) {
	ws.Handler(w, r, auth.ClaimsFromCtx(r).CompaniaID)
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
	var empleados []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var cod, nom, puesto, sitio, fv string; var activo int
			rows.Scan(&id, &cod, &nom, &puesto, &sitio, &activo, &fv)
			empleados = append(empleados, M{"DBID": id, "ID": cod, "Nombre": nom, "Puesto": puesto, "SitioTrabajo": sitio, "Activo": activo == 1, "FechaVencimiento": fv})
		}
	}
	render(w, "admin/empleados.html", M{"Claims": claims, "Empleados": empleados, "Busq": busq, "Ok": r.URL.Query().Get("ok") == "1", "Error": r.URL.Query().Get("e")})
}

func handlerEmpleadoNuevoGet(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.crear") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	sitios := listarSitiosDB(compDB)
	render(w, "admin/empleado_form.html", M{"Claims": claims, "Emp": M{}, "Sitios": sitios, "Titulo": "Nuevo Empleado", "Accion": "/desar/empleados/nuevo"})
}

func handlerEmpleadoNuevoPost(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.crear") { http.Error(w, "403", 403); return }
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	cod := r.FormValue("codigo_empleado")
	if cod == "" { http.Redirect(w, r, "/desar/empleados/nuevo?e=Código+requerido", 302); return }
	_, err := compDB.Exec(q(`INSERT INTO empleados(codigo_empleado,nombre,puesto,sitio_trabajo,telefono,
		telefono_emergencia,rfc,seguro_social,numero_identificacion,fecha_nacimiento,
		fecha_alta,fecha_vencimiento,tipo_sangre,direccion,ciudad,estado,pais,codigo_postal,notas,activo,sync_status)
		VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,1,0)`),
		cod, r.FormValue("nombre"), r.FormValue("puesto"), r.FormValue("sitio_trabajo"),
		r.FormValue("telefono"), r.FormValue("telefono_emergencia"), r.FormValue("rfc"),
		r.FormValue("seguro_social"), r.FormValue("numero_identificacion"),
		r.FormValue("fecha_nacimiento"), r.FormValue("fecha_alta"), r.FormValue("fecha_vencimiento"),
		r.FormValue("tipo_sangre"), r.FormValue("direccion"), r.FormValue("ciudad"),
		r.FormValue("estado"), r.FormValue("pais"), r.FormValue("codigo_postal"), r.FormValue("notas"))
	if err != nil { http.Redirect(w, r, "/desar/empleados/nuevo?e="+err.Error(), 302); return }
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear", "empleados", 0, cod, r.RemoteAddr)
	http.Redirect(w, r, "/desar/empleados?ok=1", 302)
}

func handlerEmpleadoEditarGet(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var e struct {
		DBID int64; CodigoEmpleado, Nombre, Puesto, SitioTrabajo, Telefono, TelefonoEmergencia string
		RFC, SeguroSocial, NumeroIdentificacion, FechaNacimiento, FechaAlta, FechaVencimiento  string
		TipoSangre, Direccion, Ciudad, Estado, Pais, CodigoPostal, Notas                       string
		Activo int
	}
	err := compDB.QueryRow(q(`SELECT id,codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),
		COALESCE(telefono,''),COALESCE(telefono_emergencia,''),COALESCE(rfc,''),COALESCE(seguro_social,''),
		COALESCE(numero_identificacion,''),COALESCE(fecha_nacimiento,''),COALESCE(fecha_alta,''),
		COALESCE(fecha_vencimiento,''),COALESCE(tipo_sangre,''),COALESCE(direccion,''),COALESCE(ciudad,''),
		COALESCE(estado,''),COALESCE(pais,''),COALESCE(codigo_postal,''),COALESCE(notas,''),activo
		FROM empleados WHERE id=$1`), id).
		Scan(&e.DBID, &e.CodigoEmpleado, &e.Nombre, &e.Puesto, &e.SitioTrabajo,
			&e.Telefono, &e.TelefonoEmergencia, &e.RFC, &e.SeguroSocial, &e.NumeroIdentificacion,
			&e.FechaNacimiento, &e.FechaAlta, &e.FechaVencimiento, &e.TipoSangre,
			&e.Direccion, &e.Ciudad, &e.Estado, &e.Pais, &e.CodigoPostal, &e.Notas, &e.Activo)
	if err != nil { http.Error(w, "Empleado no encontrado", 404); return }
	sitios := listarSitiosDB(compDB)
	render(w, "admin/empleado_form.html", M{"Claims": claims, "Emp": e, "Sitios": sitios,
		"Titulo": "Editar Empleado", "Accion": fmt.Sprintf("/desar/empleados/%d/editar", id), "EsEdicion": true})
}

func handlerEmpleadoEditarPost(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	compDB.Exec(q(`UPDATE empleados SET nombre=$1,puesto=$2,sitio_trabajo=$3,telefono=$4,
		telefono_emergencia=$5,rfc=$6,seguro_social=$7,numero_identificacion=$8,
		fecha_nacimiento=$9,fecha_alta=$10,fecha_vencimiento=$11,tipo_sangre=$12,
		direccion=$13,ciudad=$14,estado=$15,pais=$16,codigo_postal=$17,notas=$18,sync_status=0
		WHERE id=$19`),
		r.FormValue("nombre"), r.FormValue("puesto"), r.FormValue("sitio_trabajo"),
		r.FormValue("telefono"), r.FormValue("telefono_emergencia"), r.FormValue("rfc"),
		r.FormValue("seguro_social"), r.FormValue("numero_identificacion"),
		r.FormValue("fecha_nacimiento"), r.FormValue("fecha_alta"), r.FormValue("fecha_vencimiento"),
		r.FormValue("tipo_sangre"), r.FormValue("direccion"), r.FormValue("ciudad"),
		r.FormValue("estado"), r.FormValue("pais"), r.FormValue("codigo_postal"), r.FormValue("notas"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "editar", "empleados", id, "", r.RemoteAddr)
	http.Redirect(w, r, "/desar/empleados?ok=1", 302)
}

func handlerEmpleadoBaja(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "empleados.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	compDB.Exec(q("UPDATE empleados SET activo=0,sync_status=0 WHERE id=$1"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "baja", "empleados", id, "", r.RemoteAddr)
	w.WriteHeader(200)
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
	var registros []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var cod, nom, tipo, ts, sitio, metodo string
			rows.Scan(&id, &cod, &nom, &tipo, &ts, &sitio, &metodo)
			registros = append(registros, M{"ID": id, "CodigoEmpleado": cod, "NombreEmpleado": nom, "Tipo": tipo, "Timestamp": ts, "SitioTrabajo": sitio, "Metodo": metodo})
		}
	}
	render(w, "admin/registros.html", M{"Claims": claims, "Registros": registros, "Desde": desde, "Hasta": hasta, "Emp": emp, "Ok": r.URL.Query().Get("ok") == "1"})
}

func handlerRegistrosHoy(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	hoy := time.Now().Format("2006-01-02")
	rows, _ := compDB.Query(q("SELECT codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,'') FROM registros WHERE timestamp LIKE $1 ORDER BY timestamp DESC"), hoy+"%")
	var data []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var cod, nom, tipo, ts, sitio string
			rows.Scan(&cod, &nom, &tipo, &ts, &sitio)
			data = append(data, M{"cod": cod, "nom": nom, "tipo": tipo, "ts": ts, "sitio": sitio})
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

func handlerRegistroNuevoGet(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "registros.crear") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	rows, _ := compDB.Query("SELECT codigo_empleado, nombre FROM empleados WHERE activo=1 ORDER BY nombre")
	var empleados []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var cod, nom string; rows.Scan(&cod, &nom)
			empleados = append(empleados, M{"CodigoEmpleado": cod, "Nombre": nom})
		}
	}
	sitios := listarSitiosDB(compDB)
	render(w, "admin/registro_form.html", M{"Claims": claims, "Empleados": empleados, "Sitios": sitios, "Hoy": time.Now().Format("2006-01-02T15:04")})
}

func handlerRegistroNuevoPost(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "registros.crear") { http.Error(w, "403", 403); return }
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	cod := r.FormValue("codigo_empleado"); tipo := r.FormValue("tipo")
	ts  := r.FormValue("timestamp");       sitio := r.FormValue("sitio_trabajo")
	if ts == "" { ts = time.Now().Format("2006-01-02T15:04:05") }
	var nom string; var empID int64
	compDB.QueryRow(q("SELECT id, nombre FROM empleados WHERE codigo_empleado=$1"), cod).Scan(&empID, &nom)
	if empID == 0 { http.Redirect(w, r, "/desar/registros/nuevo?e=Empleado+no+encontrado", 302); return }
	compDB.Exec(q("INSERT INTO registros(empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,sitio_trabajo,metodo,sync_status) VALUES($1,$2,$3,$4,$5,$6,'manual',1)"),
		empID, cod, nom, tipo, ts, sitio)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear", "registros", 0, cod+"/"+tipo, r.RemoteAddr)
	http.Redirect(w, r, "/desar/registros?ok=1", 302)
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
	rows, _ := compDB.Query("SELECT id,nombre,COALESCE(descripcion,''),gps_lat,gps_lon,geofence_radio_metros,COALESCE(geofence_tipo,''),geofence_activo,COALESCE(tipo_sitio,''),recibir_advertencias,activo FROM sitios ORDER BY nombre")
	var sitios []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var nom, desc, geoTipo, tipoSitio string
			var lat, lon, radio float64; var geoAct, advert, activo int
			rows.Scan(&id, &nom, &desc, &lat, &lon, &radio, &geoTipo, &geoAct, &tipoSitio, &advert, &activo)
			sitios = append(sitios, M{"ID": id, "Nombre": nom, "Descripcion": desc, "GPSLat": lat, "GPSLon": lon,
				"GeofenceRadioMetros": radio, "GeofenceTipo": geoTipo, "GeofenceActivo": geoAct == 1,
				"TipoSitio": tipoSitio, "RecibirAdvertencias": advert == 1, "Activo": activo == 1})
		}
	}
	render(w, "admin/sitios.html", M{"Claims": claims, "Sitios": sitios, "Ok": r.URL.Query().Get("ok") == "1"})
}

func handlerSitioNuevoGet(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "sitios.crear") { http.Error(w, "403", 403); return }
	render(w, "admin/sitio_form.html", M{"Claims": claims, "Sitio": M{}, "Titulo": "Nuevo Sitio", "Accion": "/desar/sitios/nuevo"})
}

func handlerSitioNuevoPost(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "sitios.crear") { http.Error(w, "403", 403); return }
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	lat, _ := strconv.ParseFloat(r.FormValue("gps_lat"), 64)
	lon, _ := strconv.ParseFloat(r.FormValue("gps_lon"), 64)
	radio, _ := strconv.ParseFloat(r.FormValue("geofence_radio_metros"), 64)
	if radio == 0 { radio = 100 }
	geoTipo := r.FormValue("geofence_tipo"); if geoTipo == "" { geoTipo = "permitido" }
	tipoSitio := r.FormValue("tipo_sitio"); if tipoSitio == "" { tipoSitio = "normal" }
	_, err := compDB.Exec(q("INSERT INTO sitios(nombre,descripcion,gps_lat,gps_lon,geofence_radio_metros,geofence_tipo,geofence_activo,tipo_sitio,recibir_advertencias,activo) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,1)"),
		r.FormValue("nombre"), r.FormValue("descripcion"), lat, lon, radio, geoTipo,
		checkboxInt(r, "geofence_activo"), tipoSitio, checkboxInt(r, "recibir_advertencias"))
	if err != nil { http.Redirect(w, r, "/desar/sitios/nuevo?e="+err.Error(), 302); return }
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear", "sitios", 0, r.FormValue("nombre"), r.RemoteAddr)
	http.Redirect(w, r, "/desar/sitios?ok=1", 302)
}

func handlerSitioEditarGet(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "sitios.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var sID int64; var nom, desc, geoTipo, tipoSitio string; var lat, lon, radio float64; var geoAct, advert, activo int
	compDB.QueryRow(q("SELECT id,nombre,COALESCE(descripcion,''),gps_lat,gps_lon,geofence_radio_metros,COALESCE(geofence_tipo,'permitido'),geofence_activo,COALESCE(tipo_sitio,'normal'),recibir_advertencias,activo FROM sitios WHERE id=$1"), id).
		Scan(&sID, &nom, &desc, &lat, &lon, &radio, &geoTipo, &geoAct, &tipoSitio, &advert, &activo)
	s := models.Sitio{ID: sID, Nombre: nom, Descripcion: desc, GPSLat: lat, GPSLon: lon,
		GeofenceRadioMetros: radio, GeofenceTipo: geoTipo, GeofenceActivo: geoAct == 1,
		TipoSitio: tipoSitio, RecibirAdvertencias: advert == 1, Activo: activo == 1}
	render(w, "admin/sitio_form.html", M{"Claims": claims, "Sitio": s, "Titulo": "Editar Sitio", "Accion": fmt.Sprintf("/desar/sitios/%d/editar", id), "EsEdicion": true})
}

func handlerSitioEditarPost(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "sitios.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	lat, _ := strconv.ParseFloat(r.FormValue("gps_lat"), 64)
	lon, _ := strconv.ParseFloat(r.FormValue("gps_lon"), 64)
	radio, _ := strconv.ParseFloat(r.FormValue("geofence_radio_metros"), 64)
	compDB.Exec(q("UPDATE sitios SET nombre=$1,descripcion=$2,gps_lat=$3,gps_lon=$4,geofence_radio_metros=$5,geofence_tipo=$6,geofence_activo=$7,tipo_sitio=$8,recibir_advertencias=$9 WHERE id=$10"),
		r.FormValue("nombre"), r.FormValue("descripcion"), lat, lon, radio,
		r.FormValue("geofence_tipo"), checkboxInt(r, "geofence_activo"),
		r.FormValue("tipo_sitio"), checkboxInt(r, "recibir_advertencias"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "editar", "sitios", id, "", r.RemoteAddr)
	http.Redirect(w, r, "/desar/sitios?ok=1", 302)
}

func handlerSitioEliminar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "sitios.eliminar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	compDB.Exec(q("DELETE FROM sitios WHERE id=$1"), id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "eliminar", "sitios", id, "", r.RemoteAddr)
	w.WriteHeader(200)
}

// ── Config ────────────────────────────────────────────────────
func handlerConfig(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "config.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var nom, he, hs string; var tol int
	compDB.QueryRow("SELECT nombre_compania,hora_entrada_default,hora_salida_default,tolerancia_minutos FROM configuracion WHERE id=1").Scan(&nom, &he, &hs, &tol)
	render(w, "admin/config.html", M{"Claims": claims, "NombreCompania": nom, "HoraEntrada": he, "HoraSalida": hs, "Tolerancia": tol, "Ok": r.URL.Query().Get("ok") == "1"})
}

func handlerConfigSave(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "config.editar") { http.Error(w, "403", 403); return }
	r.ParseForm()
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	tol, _ := strconv.Atoi(r.FormValue("tolerancia"))
	nom := r.FormValue("nombre_compania")
	he2  := r.FormValue("hora_entrada")
	hs2  := r.FormValue("hora_salida")
	var cfgCount int
	compDB.QueryRow("SELECT COUNT(*) FROM configuracion WHERE id=1").Scan(&cfgCount)
	if cfgCount > 0 {
		compDB.Exec(q("UPDATE configuracion SET nombre_compania=$1,hora_entrada_default=$2,hora_salida_default=$3,tolerancia_minutos=$4 WHERE id=1"), nom, he2, hs2, tol)
	} else {
		compDB.Exec(q("INSERT INTO configuracion(id,nombre_compania,hora_entrada_default,hora_salida_default,tolerancia_minutos) VALUES(1,$1,$2,$3,$4)"), nom, he2, hs2, tol)
	}
	http.Redirect(w, r, "/desar/config?ok=1", 302)
}

// ── Usuarios ──────────────────────────────────────────────────
func handlerUsuarios(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.ver") { http.Error(w, "403", 403); return }
	rows, _ := db.Get().AdminDB().Query(q("SELECT id,nombre,email,rol,activo,COALESCE(ultimo_login,'') FROM usuarios WHERE compania_id=$1 ORDER BY nombre"), claims.CompaniaID)
	var usuarios []M
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var id int64; var nom, email, rol, ul string; var act int
			rows.Scan(&id, &nom, &email, &rol, &act, &ul)
			usuarios = append(usuarios, M{"ID": id, "Nombre": nom, "Email": email, "Rol": rol, "Activo": act == 1, "UltimoLogin": ul})
		}
	}
	render(w, "admin/usuarios.html", M{"Claims": claims, "Usuarios": usuarios, "Roles": auth.RolesDisponibles(claims.Rol), "Ok": r.URL.Query().Get("ok") == "1"})
}

func handlerUsuarioCrear(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.crear") { http.Error(w, "403", 403); return }
	r.ParseForm()
	rol := r.FormValue("rol")
	if !rolPermitido(claims.Rol, rol) { http.Error(w, "403 rol no permitido", 403); return }
	nom, email, pw := r.FormValue("nombre"), r.FormValue("email"), r.FormValue("password")
	if nom == "" || email == "" || pw == "" { http.Error(w, "campos requeridos", 400); return }
	hash, _ := auth.HashPassword(pw)
	db.Get().AdminDB().Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,$5)"), claims.CompaniaID, nom, email, hash, rol)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear_usuario", "usuarios", 0, email, r.RemoteAddr)
	http.Redirect(w, r, "/desar/usuarios?ok=1", 302)
}

func handlerUsuarioEditar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.editar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	rol := r.FormValue("rol")
	if !rolPermitido(claims.Rol, rol) { http.Error(w, "403 rol no permitido", 403); return }
	db.Get().AdminDB().Exec(q("UPDATE usuarios SET nombre=$1,rol=$2 WHERE id=$3 AND compania_id=$4"), r.FormValue("nombre"), rol, id, claims.CompaniaID)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "editar_usuario", "usuarios", id, rol, r.RemoteAddr)
	http.Redirect(w, r, "/desar/usuarios?ok=1", 302)
}

func handlerUsuarioEliminar(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "usuarios.eliminar") { http.Error(w, "403", 403); return }
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if id == claims.UserID { http.Error(w, "no puedes eliminar tu cuenta", 400); return }
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
	render(w, "admin/reportes.html", M{"Claims": auth.ClaimsFromCtx(r)})
}

func handlerReportesCSV(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "reportes.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().AddDate(0, 0, -30).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	rows, err := compDB.Query(q("SELECT codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,''),metodo,COALESCE(CAST(gps_lat AS TEXT),''),COALESCE(CAST(gps_lon AS TEXT),''),COALESCE(notas,'') FROM registros WHERE timestamp >= $1 AND timestamp <= $2 ORDER BY timestamp DESC"),
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
		if rows != nil { defer rows.Close()
			for rows.Next() {
				var cod, nom, puesto, sitio, imss, fa, fv string; var act int
				rows.Scan(&cod, &nom, &puesto, &sitio, &imss, &fa, &fv, &act)
				estado := "Activo"; if act == 0 { estado = "Baja" }
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", cod, nom, puesto, sitio, imss, fa, fv, estado)
			}
		}
	default: // asistencias
		w.Write([]byte("Código\tNombre\tFecha\tHora\tTipo\tMétodo\tSitio\n"))
		rows, _ := compDB.Query(q("SELECT codigo_empleado,nombre_empleado,date(timestamp),strftime('%H:%M:%S',timestamp),tipo,metodo,COALESCE(sitio_trabajo,'') FROM registros WHERE timestamp >= $1 AND timestamp <= $2 ORDER BY timestamp DESC"),
			desde+"T00:00:00", hasta+"T23:59:59")
		if rows != nil { defer rows.Close()
			for rows.Next() {
				var cod, nom, fecha, hora, tipo2, metodo, sitio string
				rows.Scan(&cod, &nom, &fecha, &hora, &tipo2, &metodo, &sitio)
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", cod, nom, fecha, hora, tipo2, metodo, sitio)
			}
		}
	}
}

func handlerReporteTipo(w http.ResponseWriter, r *http.Request) {
	render(w, "admin/reporte_tipo.html", M{"Claims": auth.ClaimsFromCtx(r), "Tipo": chi.URLParam(r, "tipo")})
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
	if rows != nil { defer rows.Close()
		for rows.Next() {
			var e pdf.EmpleadoGafete
			rows.Scan(&e.Codigo, &e.Nombre, &e.Puesto, &e.Sitio)
			e.QRData = e.Codigo; lista = append(lista, e)
		}
	}
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

// ── PDF Registros ─────────────────────────────────────────────
func handlerPDFRegistros(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "pdf.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().AddDate(0, 0, -14).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	var compNom string
	compDB.QueryRow("SELECT COALESCE(nombre_compania,'DESAR') FROM configuracion WHERE id=1").Scan(&compNom)
	data, err := pdf.GenerarRegistros(compDB, compNom, desde+"T00:00:00", hasta+"T23:59:59")
	if err != nil { http.Error(w, "Error PDF: "+err.Error(), 500); return }
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="registros_%s_%s.pdf"`, desde, hasta))
	w.Write(data)
}

// ── PDF Tardanzas y Ausencias ─────────────────────────────────
func handlerPDFTardanzas(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "pdf.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().AddDate(0, 0, -30).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	var compNom, horaEntrada string; var tolerancia int
	compDB.QueryRow("SELECT COALESCE(nombre_compania,'DESAR'),COALESCE(hora_entrada_default,'08:00'),COALESCE(tolerancia_minutos,15) FROM configuracion WHERE id=1").
		Scan(&compNom, &horaEntrada, &tolerancia)
	data, err := pdf.GenerarTardanzas(compDB, compNom, desde, hasta, horaEntrada, tolerancia)
	if err != nil { http.Error(w, "Error PDF: "+err.Error(), 500); return }
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="tardanzas_%s_%s.pdf"`, desde, hasta))
	w.Write(data)
}

// ── PDF Catálogo QR ───────────────────────────────────────────
func handlerPDFCatalogoQR(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "pdf.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	var compNom string
	compDB.QueryRow("SELECT COALESCE(nombre_compania,'DESAR') FROM configuracion WHERE id=1").Scan(&compNom)
	rows, _ := compDB.Query("SELECT codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,'') FROM empleados WHERE activo=1 ORDER BY nombre")
	var lista []pdf.EmpleadoGafete
	if rows != nil { defer rows.Close()
		for rows.Next() {
			var e pdf.EmpleadoGafete
			rows.Scan(&e.Codigo, &e.Nombre, &e.Puesto, &e.Sitio)
			e.QRData = "CHECADOR:" + e.Codigo + ":" + e.Nombre
			lista = append(lista, e)
		}
	}
	data, err := pdf.GenerarCatalogoQR(lista, compNom)
	if err != nil { http.Error(w, "Error PDF: "+err.Error(), 500); return }
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", `attachment; filename="catalogo-qr.pdf"`)
	w.Write(data)
}

// ── Excel Tardanzas/Ausencias ─────────────────────────────────
func handlerExcelTardanzas(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "reportes.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().AddDate(0, 0, -30).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	var horaEntrada string; var tolerancia int
	compDB.QueryRow("SELECT COALESCE(hora_entrada_default,'08:00'),COALESCE(tolerancia_minutos,15) FROM configuracion WHERE id=1").
		Scan(&horaEntrada, &tolerancia)

	// Obtener jornadas del rango
	rows, err := compDB.Query(q(`SELECT codigo_empleado,nombre_empleado,COALESCE(entrada_timestamp,''),
		COALESCE(salida_timestamp,''),COALESCE(horas_trabajadas,0),completa,COALESCE(sitio_trabajo,'')
		FROM jornadas WHERE fecha >= $1 AND fecha <= $2 ORDER BY nombre_empleado,fecha`), desde, hasta)
	if err != nil { http.Error(w, "BD error", 500); return }
	defer rows.Close()

	type JornadaRow struct { Cod, Nom, Entrada, Salida, Sitio string; Horas float64; Completa int }
	byEmp := map[string][]JornadaRow{}
	for rows.Next() {
		var j JornadaRow
		rows.Scan(&j.Cod, &j.Nom, &j.Entrada, &j.Salida, &j.Horas, &j.Completa, &j.Sitio)
		byEmp[j.Cod] = append(byEmp[j.Cod], j)
	}

	// Empleados activos
	erows, _ := compDB.Query("SELECT codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,'') FROM empleados WHERE activo=1 ORDER BY nombre")
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="tardanzas_%s_%s.csv"`, desde, hasta))
	w.Write([]byte("\xEF\xBB\xBF"))
	w.Write([]byte("Código,Nombre,Tardanzas,Ausencias,Días Trab,Horas Tot,Puesto,Área\n"))
	if erows != nil {
		defer erows.Close()
		for erows.Next() {
			var cod, nom, puesto, sitio string
			erows.Scan(&cod, &nom, &puesto, &sitio)
			js := byEmp[cod]
			tardanzas, ausencias, diasTrab := 0, 0, 0
			var horasTot float64
			partes := func(s string) (int, int) {
				var h, m int; fmt.Sscanf(s, "%d:%d", &h, &m); return h, m
			}
			hE, mE := partes(horaEntrada)
			for _, j := range js {
				if j.Entrada == "" { ausencias++; continue }
				if j.Completa == 1 { diasTrab++ }
				horasTot += j.Horas
				t, err2 := time.Parse("2006-01-02T15:04:05", j.Entrada)
				if err2 != nil { t, _ = time.Parse(time.RFC3339, j.Entrada) }
				limite := time.Date(t.Year(), t.Month(), t.Day(), hE, mE, 0, 0, t.Location())
				if t.After(limite.Add(time.Duration(tolerancia) * time.Minute)) { tardanzas++ }
			}
			fmt.Fprintf(w, "%s,%s,%d,%d,%d,%.1f,%s,%s\n",
				cod, nom, tardanzas, ausencias, diasTrab, horasTot, puesto, sitio)
		}
	}
}

// ── Excel Registros individuales ─────────────────────────────
func handlerExcelRegistros(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "reportes.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta"); emp := r.URL.Query().Get("empleado")
	if desde == "" { desde = time.Now().AddDate(0, 0, -14).Format("2006-01-02") }
	if hasta == "" { hasta = time.Now().Format("2006-01-02") }
	baseQ := `SELECT codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,''),metodo,
		COALESCE(CAST(gps_lat AS TEXT),'0'),COALESCE(CAST(gps_lon AS TEXT),'0'),COALESCE(notas,'')
		FROM registros WHERE timestamp >= $1 AND timestamp <= $2`
	args := []interface{}{desde + "T00:00:00", hasta + "T23:59:59"}
	if emp != "" { baseQ += " AND (codigo_empleado=$3 OR nombre_empleado LIKE $4)"; args = append(args, emp, "%"+emp+"%") }
	baseQ += " ORDER BY timestamp ASC"
	rows, err := compDB.Query(q(baseQ), args...)
	if err != nil { http.Error(w, "BD error", 500); return }
	defer rows.Close()
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="registros_%s_%s.csv"`, desde, hasta))
	w.Write([]byte("\xEF\xBB\xBF"))
	w.Write([]byte("Código,Nombre,Tipo,Fecha,Hora,Sitio,Método,GPS_Lat,GPS_Lon,Notas\n"))
	for rows.Next() {
		var cod, nom, tipo, ts, sitio, metodo, lat, lon, notas string
		rows.Scan(&cod, &nom, &tipo, &ts, &sitio, &metodo, &lat, &lon, &notas)
		fecha, hora := "", ""
		if len(ts) >= 19 { fecha = ts[:10]; hora = ts[11:19] }
		fmt.Fprintf(w, "%s,%s,%s,%s,%s,%s,%s,%s,%s,%q\n", cod, nom, tipo, fecha, hora, sitio, metodo, lat, lon, notas)
	}
}

// ── Excel Catálogo (gafetes o QR) ────────────────────────────
func handlerExcelCatalogo(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	if !auth.Puede(claims.Rol, "reportes.ver") { http.Error(w, "403", 403); return }
	compDB, _ := db.Get().CompanyDB(claims.CompaniaID)
	tipo := r.URL.Query().Get("tipo") // "gafetes" | "qr"
	rows, _ := compDB.Query(`SELECT codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),
		COALESCE(seguro_social,''),COALESCE(rfc,''),COALESCE(numero_identificacion,''),
		COALESCE(tipo_sangre,''),COALESCE(telefono,''),COALESCE(fecha_alta,''),COALESCE(fecha_vencimiento,''),activo
		FROM empleados ORDER BY nombre`)
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	fname := "catalogo-gafetes.csv"; if tipo == "qr" { fname = "catalogo-qr.csv" }
	w.Header().Set("Content-Disposition", `attachment; filename="`+fname+`"`)
	w.Write([]byte("\xEF\xBB\xBF"))
	if tipo == "qr" {
		w.Write([]byte("Código,Nombre,Puesto,Contenido QR,Alta,Vencimiento\n"))
	} else {
		w.Write([]byte("Código,Nombre,Puesto,Área,Alta,Vencimiento,IMSS,RFC,ID,Sangre,Teléfono,Estado\n"))
	}
	if rows != nil {
		defer rows.Close()
		for rows.Next() {
			var cod, nom, puesto, sitio, imss, rfc, numid, sangre, tel, fa, fv string; var act int
			rows.Scan(&cod, &nom, &puesto, &sitio, &imss, &rfc, &numid, &sangre, &tel, &fa, &fv, &act)
			estado := "Activo"; if act == 0 { estado = "Baja" }
			if tipo == "qr" {
				qr := "CHECADOR:" + cod + ":" + nom
				fmt.Fprintf(w, "%s,%s,%s,%q,%s,%s\n", cod, nom, puesto, qr, fa, fv)
			} else {
				fmt.Fprintf(w, "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
					cod, nom, puesto, sitio, fa, fv, imss, rfc, numid, sangre, tel, estado)
			}
		}
	}
}

// ── Superadmin ────────────────────────────────────────────────
func handlerSACompanias(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	rows, _ := db.Get().AdminDB().Query("SELECT id,nombre,plan,activo,api_key,COALESCE(fecha_vence,'') FROM companias ORDER BY id")
	var companias []M
	if rows != nil { defer rows.Close()
		for rows.Next() {
			var id int64; var nom, plan, apikey, fv string; var act int
			rows.Scan(&id, &nom, &plan, &act, &apikey, &fv)
			companias = append(companias, M{"ID": id, "Nombre": nom, "Plan": plan, "Activo": act == 1, "APIKey": apikey, "FechaVence": fv})
		}
	}
	render(w, "superadmin/companias.html", M{"Claims": claims, "Companias": companias})
}

func handlerSACrearCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	r.ParseForm()
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
	http.Redirect(w, r, "/desar/sa/companias", 302)
}

func handlerSAEditarCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	maxEmp, _ := strconv.Atoi(r.FormValue("max_empleados")); if maxEmp == 0 { maxEmp = 25 }
	db.Get().AdminDB().Exec(q("UPDATE companias SET nombre=$1,plan=$2,email=$3,fecha_vence=$4,max_empleados=$5 WHERE id=$6"),
		r.FormValue("nombre"), r.FormValue("plan"), r.FormValue("email"), r.FormValue("fecha_vence"), maxEmp, id)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "editar", "companias", id, "", r.RemoteAddr)
	http.Redirect(w, r, fmt.Sprintf("/desar/sa/companias/%d", id), 302)
}

func handlerSACompaniaDetalle(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	var c struct{ ID int64; Nombre, Plan, APIKey, Email, FechaVence string; Activo, MaxEmp int }
	db.Get().AdminDB().QueryRow(q("SELECT id,nombre,plan,api_key,COALESCE(email,''),activo,COALESCE(fecha_vence,''),max_empleados FROM companias WHERE id=$1"), id).
		Scan(&c.ID, &c.Nombre, &c.Plan, &c.APIKey, &c.Email, &c.Activo, &c.FechaVence, &c.MaxEmp)
	compDB, _ := db.Get().CompanyDB(id)
	var totalEmp, totalReg int
	if compDB != nil {
		compDB.QueryRow("SELECT COUNT(*) FROM empleados").Scan(&totalEmp)
		compDB.QueryRow("SELECT COUNT(*) FROM registros").Scan(&totalReg)
	}
	render(w, "superadmin/compania_detalle.html", M{"Claims": claims, "C": c, "TotalEmp": totalEmp, "TotalReg": totalReg, "Planes": []string{"basico", "estandar", "enterprise"}})
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
	var lista []M
	if rows != nil { defer rows.Close()
		for rows.Next() {
			var dbid int64; var cod, nom, puesto, sitio string; var act int
			rows.Scan(&dbid, &cod, &nom, &puesto, &sitio, &act)
			lista = append(lista, M{"DBID": dbid, "ID": cod, "Nombre": nom, "Puesto": puesto, "SitioTrabajo": sitio, "Activo": act == 1})
		}
	}
	render(w, "superadmin/compania_empleados.html", M{"Claims": claims, "Empleados": lista, "CompaniaID": id, "CompaniaNombre": nombre})
}

func handlerSARegistrosCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	id, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	compDB, _ := db.Get().CompanyDB(id)
	var nombre string
	db.Get().AdminDB().QueryRow(q("SELECT nombre FROM companias WHERE id=$1"), id).Scan(&nombre)
	desde := r.URL.Query().Get("desde"); hasta := r.URL.Query().Get("hasta")
	if desde == "" { desde = time.Now().Format("2006-01-02") }; if hasta == "" { hasta = desde }
	rows, _ := compDB.Query(q("SELECT id,codigo_empleado,nombre_empleado,tipo,timestamp,COALESCE(sitio_trabajo,''),metodo FROM registros WHERE timestamp >= $1 AND timestamp <= $2 ORDER BY timestamp DESC LIMIT 500"),
		desde+"T00:00:00", hasta+"T23:59:59")
	var lista []M
	if rows != nil { defer rows.Close()
		for rows.Next() {
			var dbid int64; var cod, nom, tipo, ts, sitio, metodo string
			rows.Scan(&dbid, &cod, &nom, &tipo, &ts, &sitio, &metodo)
			lista = append(lista, M{"ID": dbid, "CodigoEmpleado": cod, "NombreEmpleado": nom, "Tipo": tipo, "Timestamp": ts, "SitioTrabajo": sitio, "Metodo": metodo})
		}
	}
	render(w, "superadmin/compania_registros.html", M{"Claims": claims, "Registros": lista, "CompaniaID": id, "CompaniaNombre": nombre, "Desde": desde, "Hasta": hasta})
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
	var lista []M
	if rows != nil { defer rows.Close()
		for rows.Next() {
			var id int64; var nom, email, rol string; var act int
			rows.Scan(&id, &nom, &email, &rol, &act)
			lista = append(lista, M{"ID": id, "Nombre": nom, "Email": email, "Rol": rol, "Activo": act == 1})
		}
	}
	render(w, "superadmin/compania_usuarios.html", M{"Claims": claims, "Usuarios": lista, "CompaniaID": compID, "CompaniaNombre": compNom, "Roles": auth.Roles})
}

func handlerSACrearUsuarioCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	r.ParseForm()
	nom, email, pw, rol := r.FormValue("nombre"), r.FormValue("email"), r.FormValue("password"), r.FormValue("rol")
	if nom == "" || email == "" || pw == "" { http.Error(w, "campos requeridos", 400); return }
	hash, _ := auth.HashPassword(pw)
	db.Get().AdminDB().Exec(q("INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol) VALUES($1,$2,$3,$4,$5)"), compID, nom, email, hash, rol)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "crear_usuario", "usuarios", 0, email, r.RemoteAddr)
	http.Redirect(w, r, fmt.Sprintf("/desar/sa/companias/%d/usuarios", compID), 302)
}

func handlerSAEliminarUsuarioCompania(w http.ResponseWriter, r *http.Request) {
	claims := auth.ClaimsFromCtx(r)
	compID, _ := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	uid, _ := strconv.ParseInt(chi.URLParam(r, "uid"), 10, 64)
	db.Get().AdminDB().Exec(q("UPDATE usuarios SET activo=0 WHERE id=$1 AND compania_id=$2"), uid, compID)
	db.Get().Audit(claims.CompaniaID, claims.UserID, "desactivar_usuario", "usuarios", uid, fmt.Sprintf("cia=%d", compID), r.RemoteAddr)
	w.WriteHeader(200)
}

// ── Helpers internos ──────────────────────────────────────────
type M = map[string]interface{}

// listarSitiosDB retorna lista de sitios activos para usar en forms
func listarSitiosDB(compDB *sql.DB) []M {
	rows, err := compDB.Query("SELECT id,nombre FROM sitios WHERE activo=1 ORDER BY nombre")
	if err != nil { return nil }
	defer rows.Close()
	var sitios []M
	for rows.Next() {
		var id int64; var nom string
		rows.Scan(&id, &nom)
		sitios = append(sitios, M{"ID": id, "Nombre": nom})
	}
	return sitios
}

func render(w http.ResponseWriter, name string, data interface{}) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := tmpl.ExecuteTemplate(w, name, data); err != nil {
		http.Error(w, "template error: "+err.Error(), 500)
	}
}

func checkboxInt(r *http.Request, field string) int {
	if r.FormValue(field) != "" { return 1 }; return 0
}

func rolPermitido(rolActor, rolTarget string) bool {
	for _, r := range auth.RolesDisponibles(rolActor) { if r == rolTarget { return true } }
	return false
}
