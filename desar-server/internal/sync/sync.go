package sync

import (
	"database/sql"
	"time"

	"desar-server/internal/db"
	"desar-server/internal/models"
	"desar-server/internal/ws"
)

func q(s string)  string { return db.Q(s) }
func qi(s string) string { return db.QI(s) }

func ProcesarSync(compDB *sql.DB, adminDB *sql.DB, compID int64, req models.SyncRequest) (*models.SyncResponse, error) {
	resp := &models.SyncResponse{OK: true, Timestamp: time.Now().Format(time.RFC3339)}

	for _, reg := range req.Registros {
		_, err := compDB.Exec(qi(`INSERT INTO registros
			(empleado_id,codigo_empleado,nombre_empleado,tipo,timestamp,gps_lat,gps_lon,sitio_trabajo,metodo,notas,sync_status)
			VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,1)`),
			reg.EmpleadoID, reg.CodigoEmpleado, reg.NombreEmpleado, reg.Tipo,
			reg.Timestamp, reg.GPSLat, reg.GPSLon, reg.SitioTrabajo, reg.Metodo, reg.Notas)
		if err == nil {
			resp.RegistrosSinc++
			ws.GetHub().Broadcast(compID, &models.WSEvento{Tipo: "registro", CompaniaID: compID, Datos: reg})
		}
	}

	for _, emp := range req.Empleados {
		var exists int
		compDB.QueryRow(q("SELECT COUNT(*) FROM empleados WHERE codigo_empleado=$1"), emp.CodigoEmpleado).Scan(&exists)
		if exists > 0 {
			compDB.Exec(q(`UPDATE empleados SET
				nombre=$1,direccion=$2,ciudad=$3,estado=$4,pais=$5,codigo_postal=$6,
				telefono=$7,telefono_emergencia=$8,fecha_nacimiento=$9,rfc=$10,
				seguro_social=$11,numero_identificacion=$12,puesto=$13,tipo_sangre=$14,
				notas=$15,foto_perfil=$16,foto_rostro_1=$17,foto_rostro_2=$18,foto_rostro_3=$19,
				embedding_1=$20,embedding_2=$21,embedding_3=$22,
				sitio_trabajo=$23,activo=$24,fecha_alta=$25,fecha_vencimiento=$26,sync_status=1
				WHERE codigo_empleado=$27`),
				emp.Nombre, emp.Direccion, emp.Ciudad, emp.Estado, emp.Pais, emp.CodigoPostal,
				emp.Telefono, emp.TelefonoEmergencia, emp.FechaNacimiento, emp.RFC,
				emp.SeguroSocial, emp.NumeroIdentificacion, emp.Puesto, emp.TipoSangre,
				emp.Notas, emp.FotoPerfil, emp.FotoRostro1, emp.FotoRostro2, emp.FotoRostro3,
				emp.Embedding1, emp.Embedding2, emp.Embedding3,
				emp.SitioTrabajo, emp.Activo, emp.FechaAlta, emp.FechaVencimiento, emp.CodigoEmpleado)
		} else {
			compDB.Exec(q(`INSERT INTO empleados
				(codigo_empleado,nombre,direccion,ciudad,estado,pais,codigo_postal,
				 telefono,telefono_emergencia,fecha_nacimiento,rfc,seguro_social,
				 numero_identificacion,puesto,tipo_sangre,notas,foto_perfil,
				 foto_rostro_1,foto_rostro_2,foto_rostro_3,embedding_1,embedding_2,embedding_3,
				 sitio_trabajo,activo,fecha_alta,fecha_vencimiento,sync_status)
				VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,1)`),
				emp.CodigoEmpleado, emp.Nombre, emp.Direccion, emp.Ciudad, emp.Estado, emp.Pais, emp.CodigoPostal,
				emp.Telefono, emp.TelefonoEmergencia, emp.FechaNacimiento, emp.RFC, emp.SeguroSocial,
				emp.NumeroIdentificacion, emp.Puesto, emp.TipoSangre, emp.Notas, emp.FotoPerfil,
				emp.FotoRostro1, emp.FotoRostro2, emp.FotoRostro3, emp.Embedding1, emp.Embedding2, emp.Embedding3,
				emp.SitioTrabajo, emp.Activo, emp.FechaAlta, emp.FechaVencimiento)
		}
		resp.EmpleadosSinc++
	}

	actualizarJornadas(compDB)

	rows, err := compDB.Query(q("SELECT codigo_empleado,nombre,COALESCE(puesto,''),COALESCE(sitio_trabajo,''),activo FROM empleados WHERE sync_status=0"))
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var e models.Empleado
			rows.Scan(&e.CodigoEmpleado, &e.Nombre, &e.Puesto, &e.SitioTrabajo, &e.Activo)
			resp.EmpleadosNuevos = append(resp.EmpleadosNuevos, e)
		}
		if len(resp.EmpleadosNuevos) > 0 {
			compDB.Exec("UPDATE empleados SET sync_status=1 WHERE sync_status=0")
		}
	}

	return resp, nil
}

func actualizarJornadas(compDB *sql.DB) {
	hoy := time.Now().Format("2006-01-02")
	rows, err := compDB.Query(q("SELECT DISTINCT codigo_empleado, nombre_empleado, COALESCE(sitio_trabajo,'') FROM registros WHERE tipo='entrada' AND timestamp LIKE $1"), hoy+"%")
	if err != nil { return }
	defer rows.Close()

	for rows.Next() {
		var cod, nom, sitio string
		rows.Scan(&cod, &nom, &sitio)
		var empID int64
		compDB.QueryRow(q("SELECT id FROM empleados WHERE codigo_empleado=$1"), cod).Scan(&empID)
		if empID == 0 { continue }

		var entrada, salida string
		compDB.QueryRow(q("SELECT MIN(timestamp) FROM registros WHERE codigo_empleado=$1 AND tipo='entrada' AND timestamp LIKE $2"), cod, hoy+"%").Scan(&entrada)
		compDB.QueryRow(q("SELECT MAX(timestamp) FROM registros WHERE codigo_empleado=$1 AND tipo='salida' AND timestamp LIKE $2"), cod, hoy+"%").Scan(&salida)

		var horas float64
		var completa int
		if entrada != "" && salida != "" {
			for _, layout := range []string{"2006-01-02T15:04:05", time.RFC3339} {
				t1, e1 := time.Parse(layout, entrada)
				t2, e2 := time.Parse(layout, salida)
				if e1 == nil && e2 == nil {
					horas = t2.Sub(t1).Hours()
					if horas >= 6 { completa = 1 }
					break
				}
			}
		}

		var existe int
		compDB.QueryRow(q("SELECT COUNT(*) FROM jornadas WHERE codigo_empleado=$1 AND fecha=$2"), cod, hoy).Scan(&existe)
		if existe > 0 {
			compDB.Exec(q("UPDATE jornadas SET entrada_timestamp=$1,salida_timestamp=$2,horas_trabajadas=$3,completa=$4,sitio_trabajo=$5 WHERE codigo_empleado=$6 AND fecha=$7"),
				entrada, salida, horas, completa, sitio, cod, hoy)
		} else {
			compDB.Exec(q("INSERT INTO jornadas(empleado_id,codigo_empleado,nombre_empleado,fecha,entrada_timestamp,salida_timestamp,horas_trabajadas,completa,sitio_trabajo) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)"),
				empID, cod, nom, hoy, entrada, salida, horas, completa, sitio)
		}
	}
}
