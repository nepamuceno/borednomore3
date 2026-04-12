package pdf

import (
	"database/sql"
	"fmt"
	"time"

	"desar-server/internal/db"
	"github.com/jung-kurt/gofpdf"
)

// ── Nómina ────────────────────────────────────────────────────

type EmpleadoNomina struct {
	Codigo      string
	Nombre      string
	Puesto      string
	DiasLab     int
	HorasTrab   float64
	SalarioDia  float64
	TotalBruto  float64
	Descuentos  float64
	TotalNeto   float64
}

// GenerarNomina genera PDF de nómina para un rango de fechas.
func GenerarNomina(compDB *sql.DB, companiaNombre, desde, hasta string) ([]byte, error) {
	rows, err := compDB.Query(db.Q(`
		SELECT e.codigo_empleado, e.nombre, COALESCE(e.puesto,''),
			COUNT(DISTINCT date(r.timestamp)) AS dias,
			COALESCE(SUM(j.horas_trabajadas),0) AS horas
		FROM empleados e
		LEFT JOIN registros r ON r.codigo_empleado=e.codigo_empleado
			AND r.tipo='entrada' AND r.timestamp>=$1 AND r.timestamp<=$2
		LEFT JOIN jornadas j ON j.codigo_empleado=e.codigo_empleado
			AND j.fecha>=$3 AND j.fecha<=$4
		WHERE e.activo=1
		GROUP BY e.codigo_empleado, e.nombre, e.puesto
		ORDER BY e.nombre`),
		desde+"T00:00:00", hasta+"T23:59:59", desde[:10], hasta[:10])
	if err != nil {
		return nil, fmt.Errorf("query nomina: %w", err)
	}
	defer rows.Close()

	var empleados []EmpleadoNomina
	for rows.Next() {
		var en EmpleadoNomina
		rows.Scan(&en.Codigo, &en.Nombre, &en.Puesto, &en.DiasLab, &en.HorasTrab)
		// Salario estimado base: 200 MXN/día (configurable)
		en.SalarioDia = 200
		en.TotalBruto = float64(en.DiasLab) * en.SalarioDia
		en.Descuentos = en.TotalBruto * 0.12 // IMSS+ISR simplificado
		en.TotalNeto = en.TotalBruto - en.Descuentos
		empleados = append(empleados, en)
	}

	return renderNomina(companiaNombre, desde, hasta, empleados)
}

func renderNomina(compania, desde, hasta string, lista []EmpleadoNomina) ([]byte, error) {
	pdf := gofpdf.New("L", "mm", "Letter", "")
	pdf.SetMargins(12, 12, 12)
	pdf.AddPage()

	// Header
	pdf.SetFont("Helvetica", "B", 16)
	pdf.SetTextColor(21, 101, 192)
	pdf.CellFormat(0, 8, "NÓMINA — "+compania, "", 1, "C", false, 0, "")
	pdf.SetFont("Helvetica", "", 10)
	pdf.SetTextColor(100, 100, 100)
	pdf.CellFormat(0, 6, fmt.Sprintf("Período: %s al %s  |  Generado: %s",
		desde, hasta, time.Now().Format("02/01/2006 15:04")), "", 1, "C", false, 0, "")
	pdf.Ln(4)

	// Tabla
	cols := []struct{ title string; w float64 }{
		{"Código", 22}, {"Nombre", 60}, {"Puesto", 45},
		{"Días", 15}, {"Horas", 18},
		{"Sal/Día", 22}, {"Bruto", 25}, {"Desc.", 22}, {"Neto", 25},
	}

	// Encabezado tabla
	pdf.SetFont("Helvetica", "B", 8)
	pdf.SetFillColor(13, 65, 120)
	pdf.SetTextColor(255, 255, 255)
	for _, c := range cols {
		pdf.CellFormat(c.w, 7, c.title, "1", 0, "C", true, 0, "")
	}
	pdf.Ln(-1)

	var totalBruto, totalNeto float64
	fill := false
	for _, e := range lista {
		if fill {
			pdf.SetFillColor(240, 244, 248)
		} else {
			pdf.SetFillColor(255, 255, 255)
		}
		fill = !fill
		pdf.SetFont("Helvetica", "", 8)
		pdf.SetTextColor(33, 33, 33)
		pdf.CellFormat(cols[0].w, 6, e.Codigo, "1", 0, "L", true, 0, "")
		pdf.CellFormat(cols[1].w, 6, e.Nombre, "1", 0, "L", true, 0, "")
		pdf.CellFormat(cols[2].w, 6, e.Puesto, "1", 0, "L", true, 0, "")
		pdf.CellFormat(cols[3].w, 6, fmt.Sprintf("%d", e.DiasLab), "1", 0, "C", true, 0, "")
		pdf.CellFormat(cols[4].w, 6, fmt.Sprintf("%.1f", e.HorasTrab), "1", 0, "C", true, 0, "")
		pdf.CellFormat(cols[5].w, 6, fmt.Sprintf("$%.2f", e.SalarioDia), "1", 0, "R", true, 0, "")
		pdf.CellFormat(cols[6].w, 6, fmt.Sprintf("$%.2f", e.TotalBruto), "1", 0, "R", true, 0, "")
		pdf.CellFormat(cols[7].w, 6, fmt.Sprintf("$%.2f", e.Descuentos), "1", 0, "R", true, 0, "")
		pdf.CellFormat(cols[8].w, 6, fmt.Sprintf("$%.2f", e.TotalNeto), "1", 1, "R", true, 0, "")
		totalBruto += e.TotalBruto
		totalNeto += e.TotalNeto
	}

	// Totales
	pdf.SetFont("Helvetica", "B", 9)
	pdf.SetFillColor(13, 65, 120)
	pdf.SetTextColor(255, 255, 255)
	ancho := cols[0].w + cols[1].w + cols[2].w + cols[3].w + cols[4].w + cols[5].w
	pdf.CellFormat(ancho, 7, "TOTALES", "1", 0, "R", true, 0, "")
	pdf.CellFormat(cols[6].w, 7, fmt.Sprintf("$%.2f", totalBruto), "1", 0, "R", true, 0, "")
	pdf.CellFormat(cols[7].w, 7, fmt.Sprintf("$%.2f", totalBruto-totalNeto), "1", 0, "R", true, 0, "")
	pdf.CellFormat(cols[8].w, 7, fmt.Sprintf("$%.2f", totalNeto), "1", 1, "R", true, 0, "")

	// Footer
	pdf.Ln(8)
	pdf.SetFont("Helvetica", "I", 7)
	pdf.SetTextColor(150, 150, 150)
	pdf.CellFormat(0, 5, "DESAR — Sistema de Control de Asistencia  |  Documento generado automáticamente — no requiere firma", "", 0, "C", false, 0, "")

	var buf []byte
	w := byteWriter{data: &buf}
	err := pdf.Output(w)
	return buf, err
}

// ── Gafete CR80 ───────────────────────────────────────────────

type EmpleadoGafete struct {
	Codigo   string
	Nombre   string
	Puesto   string
	Sitio    string
	QRData   string
}

func GenerarCatalogoGafetes(empleados []EmpleadoGafete, compania string) ([]byte, error) {
	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetMargins(8, 8, 8)

	const (
		cardW  = 85.6
		cardH  = 54.0
		cols   = 2
		gapX   = 4.0
		gapY   = 4.0
		startX = 8.0
		startY = 8.0
	)

	col := 0
	row := 0
	pdf.AddPage()

	for _, e := range empleados {
		x := startX + float64(col)*(cardW+gapX)
		y := startY + float64(row)*(cardH+gapY)

		// Fondo tarjeta
		pdf.SetFillColor(13, 65, 120)
		pdf.RoundedRect(x, y, cardW, cardH, 3, "1234", "F")

		// Franja blanca inferior
		pdf.SetFillColor(255, 255, 255)
		pdf.RoundedRect(x+1, y+cardH-28, cardW-2, 27, 2, "1234", "F")

		// Nombre compañía
		pdf.SetFont("Helvetica", "B", 7)
		pdf.SetTextColor(255, 255, 255)
		pdf.SetXY(x+2, y+3)
		pdf.CellFormat(cardW-4, 5, compania, "", 1, "C", false, 0, "")

		// Código grande
		pdf.SetFont("Helvetica", "B", 18)
		pdf.SetTextColor(255, 255, 255)
		pdf.SetXY(x+2, y+9)
		pdf.CellFormat(cardW-4, 10, e.Codigo, "", 1, "C", false, 0, "")

		// QR placeholder (texto)
		pdf.SetFont("Helvetica", "", 6)
		pdf.SetTextColor(200, 220, 255)
		pdf.SetXY(x+2, y+20)
		pdf.CellFormat(cardW-4, 4, "[QR:"+e.QRData+"]", "", 1, "C", false, 0, "")

		// Nombre empleado
		pdf.SetFont("Helvetica", "B", 9)
		pdf.SetTextColor(13, 65, 120)
		pdf.SetXY(x+3, y+cardH-26)
		pdf.CellFormat(cardW-6, 6, truncate(e.Nombre, 28), "", 1, "L", false, 0, "")

		// Puesto
		pdf.SetFont("Helvetica", "", 7)
		pdf.SetTextColor(80, 80, 80)
		pdf.SetXY(x+3, y+cardH-19)
		pdf.CellFormat(cardW-6, 5, truncate(e.Puesto, 30), "", 1, "L", false, 0, "")

		// Sitio
		pdf.SetFont("Helvetica", "I", 6)
		pdf.SetTextColor(120, 120, 120)
		pdf.SetXY(x+3, y+cardH-13)
		pdf.CellFormat(cardW-6, 5, truncate(e.Sitio, 32), "", 1, "L", false, 0, "")

		// Línea decorativa
		pdf.SetDrawColor(13, 65, 120)
		pdf.SetLineWidth(0.4)
		pdf.Line(x+3, y+cardH-8, x+cardW-3, y+cardH-8)

		// DESAR footer
		pdf.SetFont("Helvetica", "I", 5)
		pdf.SetTextColor(160, 160, 160)
		pdf.SetXY(x+3, y+cardH-7)
		pdf.CellFormat(cardW-6, 4, "DESAR Control de Asistencia", "", 1, "R", false, 0, "")

		col++
		if col >= cols {
			col = 0
			row++
			if float64(row)*(cardH+gapY)+cardH > 280 {
				pdf.AddPage()
				row = 0
			}
		}
	}

	var buf []byte
	w := byteWriter{data: &buf}
	err := pdf.Output(w)
	return buf, err
}

// ── Reporte de Vigencias ──────────────────────────────────────

type EmpleadoVig struct {
	Codigo          string
	Nombre          string
	Puesto          string
	FechaVencimiento string
	DiasRestantes   int
	Estado          string
}

func GenerarReporteVigencias(compDB *sql.DB, compania string) ([]byte, error) {
	rows, err := compDB.Query(db.Q(`
		SELECT codigo_empleado, nombre, COALESCE(puesto,''), COALESCE(fecha_vencimiento,'')
		FROM empleados WHERE activo=1 AND fecha_vencimiento!='' AND fecha_vencimiento IS NOT NULL
		ORDER BY fecha_vencimiento ASC`))
	if err != nil {
		return nil, fmt.Errorf("query vigencias: %w", err)
	}
	defer rows.Close()

	hoy := time.Now()
	var lista []EmpleadoVig
	for rows.Next() {
		var ev EmpleadoVig
		rows.Scan(&ev.Codigo, &ev.Nombre, &ev.Puesto, &ev.FechaVencimiento)
		if ev.FechaVencimiento != "" {
			t, err := time.Parse("2006-01-02", ev.FechaVencimiento[:10])
			if err == nil {
				ev.DiasRestantes = int(t.Sub(hoy).Hours() / 24)
				if ev.DiasRestantes < 0 {
					ev.Estado = "VENCIDO"
				} else if ev.DiasRestantes <= 30 {
					ev.Estado = "POR VENCER"
				} else {
					ev.Estado = "VIGENTE"
				}
			}
		}
		lista = append(lista, ev)
	}
	return renderVigencias(compania, lista)
}

func renderVigencias(compania string, lista []EmpleadoVig) ([]byte, error) {
	pdf := gofpdf.New("P", "mm", "Letter", "")
	pdf.SetMargins(14, 14, 14)
	pdf.AddPage()

	pdf.SetFont("Helvetica", "B", 14)
	pdf.SetTextColor(21, 101, 192)
	pdf.CellFormat(0, 8, "REPORTE DE VIGENCIAS — "+compania, "", 1, "C", false, 0, "")
	pdf.SetFont("Helvetica", "", 9)
	pdf.SetTextColor(120, 120, 120)
	pdf.CellFormat(0, 5, "Generado: "+time.Now().Format("02/01/2006 15:04"), "", 1, "C", false, 0, "")
	pdf.Ln(3)

	// Tabla
	pdf.SetFont("Helvetica", "B", 9)
	pdf.SetFillColor(13, 65, 120)
	pdf.SetTextColor(255, 255, 255)
	ws := []float64{25, 70, 45, 30, 20}
	titles := []string{"Código", "Nombre", "Puesto", "Vencimiento", "Estado"}
	for i, t := range titles {
		pdf.CellFormat(ws[i], 7, t, "1", 0, "C", true, 0, "")
	}
	pdf.Ln(-1)

	for _, e := range lista {
		var fr, fg, fb int
		switch e.Estado {
		case "VENCIDO":
			fr, fg, fb = 198, 40, 40
		case "POR VENCER":
			fr, fg, fb = 230, 81, 0
		default:
			fr, fg, fb = 46, 125, 50
		}
		pdf.SetFont("Helvetica", "", 8)
		pdf.SetTextColor(33, 33, 33)
		pdf.SetFillColor(250, 250, 250)
		pdf.CellFormat(ws[0], 6, e.Codigo, "1", 0, "L", true, 0, "")
		pdf.CellFormat(ws[1], 6, e.Nombre, "1", 0, "L", true, 0, "")
		pdf.CellFormat(ws[2], 6, e.Puesto, "1", 0, "L", true, 0, "")
		pdf.CellFormat(ws[3], 6, e.FechaVencimiento[:10], "1", 0, "C", true, 0, "")
		pdf.SetTextColor(fr, fg, fb)
		pdf.SetFont("Helvetica", "B", 7)
		pdf.CellFormat(ws[4], 6, e.Estado, "1", 1, "C", true, 0, "")
	}

	var buf []byte
	w := byteWriter{data: &buf}
	err := pdf.Output(w)
	return buf, err
}

// ── Helpers ───────────────────────────────────────────────────

type byteWriter struct{ data *[]byte }

func (bw byteWriter) Write(p []byte) (n int, err error) {
	*bw.data = append(*bw.data, p...)
	return len(p), nil
}

func truncate(s string, max int) string {
	r := []rune(s)
	if len(r) > max {
		return string(r[:max-1]) + "…"
	}
	return s
}
