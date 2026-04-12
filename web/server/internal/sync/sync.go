package sync

import (
	"database/sql"
	"fmt"
	"time"

	"desar-server/internal/models"
	"desar-server/internal/notify"
	"desar-server/internal/ws"
)

// ProcesarSync maneja un batch del APK y retorna qué enviar de vuelta
func ProcesarSync(compDB *sql.DB, adminDB *sql.DB, compID int64, req models.SyncRequest) (*models.SyncResponse, error) {
	resp := &models.SyncResponse{
		OK:        true,
		Timestamp: time.Now().Format(time.RFC3339),
	}

	// ── Guardar registros del APK ────────────────────────
	for _, reg := range req.Registros {
		_, err := compDB.Exec(`
			INSERT OR IGNORE INTO registros
				(empleado_id, codigo_empleado, nombre_empleado, tipo,
				 timestamp, gps_lat, gps_lon, sitio_trabajo, metodo, notas, sync_status)
			VALUES (?,?,?,?,?,?,?,?,?,?,1)`,
			reg.EmpleadoID, reg.CodigoEmpleado, reg.NombreEmpleado, reg.Tipo,
			reg.Timestamp, reg.GPSLat, reg.GPSLon, reg.SitioTrabajo, reg.Metodo, reg.Notas,
		)
		if err == nil {
			resp.RegistrosSinc++

			// Broadcast tiempo real al panel
			ws.GetHub().Broadcast(compID, &models.WSEvento{
				Tipo:       "registro",
				CompaniaID: compID,
				Datos:      reg,
			})

			// Notificar si el sitio tiene advertencias activas
			notificarSiSitioRequiere(compDB, adminDB, compID, reg)
		}
	}

	// ── Guardar empleados del APK ─────────────────────────
	for _, emp := range req.Empleados {
		compDB.Exec(`
			INSERT INTO empleados
				(codigo_empleado, nombre, puesto, sitio_trabajo, seguro_social,
				 numero_identificacion, telefono, fecha_alta, fecha_vencimiento, activo)
			VALUES (?,?,?,?,?,?,?,?,?,?)
			ON CONFLICT(codigo_empleado) DO UPDATE SET
				nombre=excluded.nombre,
				puesto=excluded.puesto,
				sitio_trabajo=excluded.sitio_trabajo,
				fecha_vencimiento=excluded.fecha_vencimiento,
				activo=excluded.activo`,
			emp.CodigoEmpleado, emp.Nombre, emp.Puesto, emp.SitioTrabajo,
			emp.SeguroSocial, emp.NumeroIdentificacion, emp.Telefono,
			emp.FechaAlta, emp.FechaVencimiento, emp.Activo,
		)
		resp.EmpleadosSinc++
	}

	// ── Empleados nuevos en servidor que el APK no tiene ──
	// Si el APK manda su lista de códigos conocidos, le mandamos los que faltan
	resp.EmpleadosNuevos = buscarEmpleadosNuevosParaAPK(compDB, req.Empleados)

	return resp, nil
}

// buscarEmpleadosNuevosParaAPK retorna empleados en el servidor que el APK no tiene
func buscarEmpleadosNuevosParaAPK(compDB *sql.DB, empConocidos []models.Empleado) []models.Empleado {
	if len(empConocidos) == 0 {
		return nil
	}

	// Construir lista de códigos conocidos por el APK
	conocidos := make(map[string]bool)
	for _, e := range empConocidos {
		conocidos[e.CodigoEmpleado] = true
	}

	rows, err := compDB.Query(
		"SELECT codigo_empleado, nombre, puesto, sitio_trabajo, activo, COALESCE(fecha_vencimiento,'') FROM empleados WHERE activo=1",
	)
	if err != nil {
		return nil
	}
	defer rows.Close()

	var nuevos []models.Empleado
	for rows.Next() {
		var e models.Empleado
		rows.Scan(&e.CodigoEmpleado, &e.Nombre, &e.Puesto, &e.SitioTrabajo, &e.Activo, &e.FechaVencimiento)
		if !conocidos[e.CodigoEmpleado] {
			nuevos = append(nuevos, e)
		}
	}
	return nuevos
}

// notificarSiSitioRequiere envía alerta si el sitio tiene recibir_advertencias=1
func notificarSiSitioRequiere(compDB *sql.DB, adminDB *sql.DB, compID int64, reg models.Registro) {
	if reg.SitioTrabajo == "" {
		return
	}

	var recibirAdv int
	var tipoSitio string
	err := compDB.QueryRow(
		"SELECT recibir_advertencias, COALESCE(tipo_sitio,'normal') FROM sitios WHERE nombre=? AND activo=1",
		reg.SitioTrabajo,
	).Scan(&recibirAdv, &tipoSitio)

	if err != nil || recibirAdv == 0 {
		return
	}

	// Obtener emails de admins de la compañía
	emailRows, _ := adminDB.Query(
		"SELECT email FROM usuarios WHERE compania_id=? AND activo=1 AND rol IN ('admin','gerente')",
		compID,
	)
	if emailRows == nil {
		return
	}
	defer emailRows.Close()

	var emails []string
	for emailRows.Next() {
		var e string
		emailRows.Scan(&e)
		emails = append(emails, e)
	}

	if len(emails) == 0 {
		return
	}

	dt, _ := time.Parse(time.RFC3339, reg.Timestamp)
	hora := dt.Format("15:04:05")

	emoji := "🟢"
	if reg.Tipo == "salida" {
		emoji = "🔴"
	}
	if tipoSitio == "peligroso" {
		emoji = "⚠️"
	}

	asunto := fmt.Sprintf("%s %s en %s — %s", emoji, reg.NombreEmpleado, reg.SitioTrabajo, reg.Tipo)
	html   := notify.EmailRegistro(reg.NombreEmpleado, reg.Tipo, hora, reg.SitioTrabajo)
	notify.N.Email(emails, asunto, html)

	// También broadcast WS con tipo "alerta" para el dashboard
	ws.GetHub().Broadcast(compID, &models.WSEvento{
		Tipo:       "alerta",
		CompaniaID: compID,
		Datos: map[string]string{
			"empleado": reg.NombreEmpleado,
			"tipo":     reg.Tipo,
			"sitio":    reg.SitioTrabajo,
			"tipo_sitio": tipoSitio,
		},
	})
}
