package notify

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/smtp"
	"strings"
	"time"
)

// Config se carga desde variables de entorno o BD
type Config struct {
	SMTPHost     string
	SMTPPort     string
	SMTPUser     string
	SMTPPassword string
	SMTPFrom     string
	Habilitado   bool
}

var cfg Config

func Init(c Config) {
	cfg = c
}

// ── Email ─────────────────────────────────────────────────────

func EnviarEmail(para []string, asunto, cuerpoHTML string) error {
	if !cfg.Habilitado || cfg.SMTPHost == "" {
		return nil // silencioso si no está configurado
	}
	auth := smtp.PlainAuth("", cfg.SMTPUser, cfg.SMTPPassword, cfg.SMTPHost)
	msg := buildEmail(cfg.SMTPFrom, para, asunto, cuerpoHTML)
	addr := cfg.SMTPHost + ":" + cfg.SMTPPort
	return smtp.SendMail(addr, auth, cfg.SMTPFrom, para, []byte(msg))
}

func buildEmail(from string, to []string, subject, htmlBody string) string {
	var b strings.Builder
	b.WriteString("MIME-Version: 1.0\r\n")
	b.WriteString("Content-Type: text/html; charset=UTF-8\r\n")
	b.WriteString(fmt.Sprintf("From: DESAR <%s>\r\n", from))
	b.WriteString(fmt.Sprintf("To: %s\r\n", strings.Join(to, ", ")))
	b.WriteString(fmt.Sprintf("Subject: %s\r\n", subject))
	b.WriteString("Date: " + time.Now().Format(time.RFC1123Z) + "\r\n")
	b.WriteString("\r\n")
	b.WriteString(htmlBody)
	return b.String()
}

// ── Templates de email ────────────────────────────────────────

func EmailRegistro(nombreEmp, tipo, hora, sitio string) string {
	emoji := "🟢"
	if tipo == "salida" {
		emoji = "🔴"
	}
	return fmt.Sprintf(`<!DOCTYPE html><html><body style="font-family:sans-serif;background:#F0F4F8;padding:20px">
<div style="max-width:480px;margin:auto;background:white;border-radius:12px;overflow:hidden">
  <div style="background:#1565C0;padding:20px;color:white">
    <h2 style="margin:0">DESAR — Registro de Asistencia</h2>
  </div>
  <div style="padding:24px">
    <p style="font-size:32px;margin:0">%s</p>
    <h3 style="margin:8px 0;color:#212121">%s — %s</h3>
    <p style="color:#757575">Hora: <strong>%s</strong></p>
    <p style="color:#757575">Sitio: <strong>%s</strong></p>
  </div>
  <div style="background:#F5F7FA;padding:12px 24px;font-size:11px;color:#9E9E9E">
    DESAR © 2026 zSoft
  </div>
</div>
</body></html>`, emoji, nombreEmp, strings.ToUpper(tipo), hora, sitio)
}

func EmailVencimiento(nombreEmp, codigo, fechaVence string, diasRestantes int) string {
	color := "#F57C00"
	if diasRestantes <= 0 {
		color = "#C62828"
	}
	return fmt.Sprintf(`<!DOCTYPE html><html><body style="font-family:sans-serif;background:#F0F4F8;padding:20px">
<div style="max-width:480px;margin:auto;background:white;border-radius:12px;overflow:hidden">
  <div style="background:%s;padding:20px;color:white">
    <h2 style="margin:0">⚠️ Alerta de Vencimiento</h2>
  </div>
  <div style="padding:24px">
    <p style="color:#212121">El empleado <strong>%s</strong> (código: %s)</p>
    %s
    <p style="color:#757575">Fecha de vencimiento: <strong>%s</strong></p>
    <p style="margin-top:16px">Ingresa al panel para actualizar la información.</p>
  </div>
</div>
</body></html>`,
		color, nombreEmp, codigo,
		func() string {
			if diasRestantes <= 0 {
				return "<p style='color:#C62828;font-weight:bold'>⛔ Ha VENCIDO</p>"
			}
			return fmt.Sprintf("<p style='color:#F57C00;font-weight:bold'>Vence en %d días</p>", diasRestantes)
		}(),
		fechaVence)
}

func EmailResumenSemanal(compania string, totalEmp, regSemana, tardanzas int) string {
	return fmt.Sprintf(`<!DOCTYPE html><html><body style="font-family:sans-serif;background:#F0F4F8;padding:20px">
<div style="max-width:480px;margin:auto;background:white;border-radius:12px;overflow:hidden">
  <div style="background:#1565C0;padding:20px;color:white">
    <h2 style="margin:0">📊 Resumen Semanal — %s</h2>
    <p style="margin:4px 0 0;opacity:0.8">Semana del %s</p>
  </div>
  <div style="padding:24px">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;text-align:center">
      <div style="background:#E3F2FD;border-radius:8px;padding:16px">
        <div style="font-size:28px;font-weight:bold;color:#1565C0">%d</div>
        <div style="font-size:12px;color:#757575">Empleados</div>
      </div>
      <div style="background:#E8F5E9;border-radius:8px;padding:16px">
        <div style="font-size:28px;font-weight:bold;color:#2E7D32">%d</div>
        <div style="font-size:12px;color:#757575">Registros</div>
      </div>
      <div style="background:#FFF3E0;border-radius:8px;padding:16px">
        <div style="font-size:28px;font-weight:bold;color:#E65100">%d</div>
        <div style="font-size:12px;color:#757575">Tardanzas</div>
      </div>
    </div>
  </div>
</div>
</body></html>`,
		compania,
		time.Now().AddDate(0, 0, -7).Format("02/01/2006")+" al "+time.Now().Format("02/01/2006"),
		totalEmp, regSemana, tardanzas)
}

// ── Webhook ───────────────────────────────────────────────────

type WebhookPayload struct {
	Evento     string      `json:"evento"`
	Timestamp  string      `json:"timestamp"`
	CompaniaID int64       `json:"compania_id"`
	Datos      interface{} `json:"datos"`
}

func EnviarWebhook(url string, payload WebhookPayload) error {
	if url == "" {
		return nil
	}
	payload.Timestamp = time.Now().Format(time.RFC3339)
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Post(url, "application/json", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("webhook error: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("webhook HTTP %d", resp.StatusCode)
	}
	return nil
}

// ── Notificaciones asíncronas (no bloquean el request) ────────

type Notificador struct {
	queue chan func()
}

var N = &Notificador{queue: make(chan func(), 256)}

func init() {
	go func() {
		for fn := range N.queue {
			fn()
		}
	}()
}

func (n *Notificador) Email(para []string, asunto, html string) {
	n.queue <- func() {
		if err := EnviarEmail(para, asunto, html); err != nil {
			fmt.Printf("[NOTIFY] Email error: %v\n", err)
		}
	}
}

func (n *Notificador) Webhook(url string, payload WebhookPayload) {
	n.queue <- func() {
		if err := EnviarWebhook(url, payload); err != nil {
			fmt.Printf("[NOTIFY] Webhook error: %v\n", err)
		}
	}
}

// NotificarRegistro — envía notificación de registro si está configurado
func NotificarRegistro(adminDB, compDB interface{}, compID int64, reg interface{}) {
	// Placeholder — implementación completa pendiente según configuración de cada compañía
	// La función existe para que sync.go pueda referenciarla sin errores de compilación
}
