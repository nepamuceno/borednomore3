package scheduler

import (
	"database/sql"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"desar-server/internal/notify"
)

// DBProvider provee acceso a las BDs — lo inyecta main.go
type DBProvider interface {
	AdminDB() *sql.DB
	CompanyDB(int64) (*sql.DB, error)
}

var dbp DBProvider

func Init(provider DBProvider) {
	dbp = provider
	go loop()
}

// ── Loop principal ────────────────────────────────────────────
func loop() {
	for {
		ahora := time.Now()

		// Backup a las 3:00 AM
		next3am := nextTime(3, 0)
		// Reporte semanal lunes 7:00 AM
		nextLunes7am := nextMonday7am()
		// Chequeo de vencimientos cada 24h a las 8 AM
		next8am := nextTime(8, 0)

		var nextRun time.Time
		switch {
		case next3am.Before(nextLunes7am) && next3am.Before(next8am):
			nextRun = next3am
		case nextLunes7am.Before(next8am):
			nextRun = nextLunes7am
		default:
			nextRun = next8am
		}

		fmt.Printf("[SCHED] Próxima tarea: %s\n", nextRun.Format("2006-01-02 15:04"))
		time.Sleep(time.Until(nextRun))
		ahora = time.Now()

		if ahora.Hour() == 3 && ahora.Minute() < 5 {
			ejecutarBackups()
		}
		if ahora.Weekday() == time.Monday && ahora.Hour() == 7 {
			ejecutarReporteSemanal()
		}
		if ahora.Hour() == 8 && ahora.Minute() < 5 {
			ejecutarAlertsVencimientos()
		}

		time.Sleep(6 * time.Minute) // evitar doble ejecución
	}
}

// ── Backups ───────────────────────────────────────────────────

func ejecutarBackups() {
	fmt.Println("[SCHED] Iniciando backups nocturnos...")
	adminDB := dbp.AdminDB()
	rows, err := adminDB.Query("SELECT id, db_path FROM companias WHERE activo=1")
	if err != nil {
		fmt.Printf("[SCHED] Error listando compañías: %v\n", err)
		return
	}
	defer rows.Close()

	ts := time.Now().Format("20060102")
	backed := 0

	for rows.Next() {
		var id int64
		var dbPath string
		rows.Scan(&id, &dbPath)

		backupDir := filepath.Join(filepath.Dir(dbPath), "backups")
		os.MkdirAll(backupDir, 0750)
		destino := filepath.Join(backupDir, fmt.Sprintf("company_%d_%s.db", id, ts))

		if err := copiarArchivo(dbPath, destino); err != nil {
			fmt.Printf("[SCHED] Backup company %d: %v\n", id, err)
		} else {
			backed++
		}
	}

	// Limpiar backups > 30 días
	limpiarBackupsViejos(30)

	fmt.Printf("[SCHED] Backups completados: %d compañías\n", backed)
}

func copiarArchivo(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

func limpiarBackupsViejos(dias int) {
	adminDB := dbp.AdminDB()
	rows, _ := adminDB.Query("SELECT db_path FROM companias")
	if rows == nil {
		return
	}
	defer rows.Close()

	limite := time.Now().AddDate(0, 0, -dias)
	for rows.Next() {
		var dbPath string
		rows.Scan(&dbPath)
		backupDir := filepath.Join(filepath.Dir(dbPath), "backups")
		entries, _ := os.ReadDir(backupDir)
		for _, e := range entries {
			info, _ := e.Info()
			if info != nil && info.ModTime().Before(limite) {
				os.Remove(filepath.Join(backupDir, e.Name()))
			}
		}
	}
}

// ── Alertas de vencimiento ────────────────────────────────────

func ejecutarAlertsVencimientos() {
	fmt.Println("[SCHED] Verificando vencimientos...")
	adminDB := dbp.AdminDB()

	type empresa struct {
		id     int64
		nombre string
		emails []string
	}

	rows, err := adminDB.Query("SELECT id, nombre FROM companias WHERE activo=1")
	if err != nil {
		return
	}
	defer rows.Close()

	hoy := time.Now().Format("2006-01-02")
	en30 := time.Now().AddDate(0, 0, 30).Format("2006-01-02")

	for rows.Next() {
		var compID int64
		var compNombre string
		rows.Scan(&compID, &compNombre)

		compDB, err := dbp.CompanyDB(compID)
		if err != nil {
			continue
		}

		// Empleados vencidos o por vencer en 30 días
		empRows, _ := compDB.Query(`
			SELECT nombre, codigo_empleado, fecha_vencimiento
			FROM empleados
			WHERE activo=1
			  AND fecha_vencimiento != ''
			  AND fecha_vencimiento <= ?`, en30)
		if empRows == nil {
			continue
		}

		// Obtener emails de admins de la compañía
		emailRows, _ := adminDB.Query(
			"SELECT email FROM usuarios WHERE compania_id=? AND activo=1 AND rol IN ('admin','gerente')",
			compID)
		var emails []string
		if emailRows != nil {
			defer emailRows.Close()
			for emailRows.Next() {
				var e string
				emailRows.Scan(&e)
				emails = append(emails, e)
			}
		}

		for empRows.Next() {
			var nombre, codigo, fechaVence string
			empRows.Scan(&nombre, &codigo, &fechaVence)

			dias := 0
			if fv, err := time.Parse("2006-01-02", fechaVence); err == nil {
				dias = int(time.Until(fv).Hours() / 24)
			}

			asunto := fmt.Sprintf("⚠️ Vencimiento: %s — %s", nombre, compNombre)
			if fechaVence <= hoy {
				asunto = fmt.Sprintf("⛔ VENCIDO: %s — %s", nombre, compNombre)
			}

			if len(emails) > 0 {
				html := notify.EmailVencimiento(nombre, codigo, fechaVence, dias)
				notify.N.Email(emails, asunto, html)
			}
		}
		empRows.Close()
	}
}

// ── Reporte semanal ───────────────────────────────────────────

func ejecutarReporteSemanal() {
	fmt.Println("[SCHED] Generando reportes semanales...")
	adminDB := dbp.AdminDB()

	desde := time.Now().AddDate(0, 0, -7).Format("2006-01-02")
	hasta := time.Now().Format("2006-01-02")

	rows, _ := adminDB.Query("SELECT id, nombre FROM companias WHERE activo=1")
	if rows == nil {
		return
	}
	defer rows.Close()

	for rows.Next() {
		var compID int64
		var compNombre string
		rows.Scan(&compID, &compNombre)

		compDB, err := dbp.CompanyDB(compID)
		if err != nil {
			continue
		}

		var totalEmp, regSemana, tardanzas int
		compDB.QueryRow("SELECT COUNT(*) FROM empleados WHERE activo=1").Scan(&totalEmp)
		compDB.QueryRow(`SELECT COUNT(*) FROM registros WHERE timestamp >= ? AND timestamp <= ?`,
			desde+"T00:00:00", hasta+"T23:59:59").Scan(&regSemana)

		// Tardanzas: entradas después de las 8:15 (hora + tolerancia 15min)
		compDB.QueryRow(`SELECT COUNT(*) FROM registros
			WHERE tipo='entrada' AND timestamp >= ? AND timestamp <= ?
			  AND strftime('%H:%M', timestamp) > '08:15'`,
			desde+"T00:00:00", hasta+"T23:59:59").Scan(&tardanzas)

		emailRows, _ := adminDB.Query(
			"SELECT email FROM usuarios WHERE compania_id=? AND activo=1 AND rol IN ('admin')",
			compID)
		if emailRows == nil {
			continue
		}
		var emails []string
		for emailRows.Next() {
			var e string
			emailRows.Scan(&e)
			emails = append(emails, e)
		}
		emailRows.Close()

		if len(emails) > 0 {
			html := notify.EmailResumenSemanal(compNombre, totalEmp, regSemana, tardanzas)
			notify.N.Email(emails, fmt.Sprintf("📊 Resumen semanal — %s", compNombre), html)
		}
	}
}

// ── Helpers de tiempo ─────────────────────────────────────────

func nextTime(hour, minute int) time.Time {
	now := time.Now()
	t := time.Date(now.Year(), now.Month(), now.Day(), hour, minute, 0, 0, now.Location())
	if t.Before(now) {
		t = t.AddDate(0, 0, 1)
	}
	return t
}

func nextMonday7am() time.Time {
	now := time.Now()
	daysUntilMonday := (int(time.Monday) - int(now.Weekday()) + 7) % 7
	if daysUntilMonday == 0 && now.Hour() >= 7 {
		daysUntilMonday = 7
	}
	next := time.Date(now.Year(), now.Month(), now.Day()+daysUntilMonday, 7, 0, 0, 0, now.Location())
	return next
}
