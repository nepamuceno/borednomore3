# DESAR Server — Documento de Diseño Completo
> Si se interrumpe la generación, este documento permite retomar exactamente donde se quedó.

---

## Estado actual del código

### Archivos completados ✅
```
go.mod                              → dependencias Go
internal/models/models.go           → todos los structs compartidos
internal/db/manager.go             → BD admin + BD por compañía (SQLite)
internal/auth/auth.go              → JWT, bcrypt, roles, middleware
internal/ws/hub.go                 → WebSocket hub tiempo real
internal/api/v1/handlers.go        → endpoints APK
internal/web/handlers.go           → panel web completo
cmd/server/main.go                 → entry point, dual port
web/templates/auth/login.html      → pantalla login
web/templates/admin/dashboard.html → dashboard con WebSocket live
web/templates/admin/empleados.html → lista empleados con búsqueda
web/templates/admin/registros.html → registros con filtros
web/templates/admin/sitios.html    → lista sitios
web/templates/admin/config.html    → configuración compañía
web/templates/admin/usuarios.html  → gestión usuarios del panel
web/templates/admin/reportes.html  → exportar CSV
web/templates/superadmin/companias.html         → CRUD compañías
web/templates/superadmin/compania_detalle.html  → detalle + API key
web/static/css/main.css            → CSS completo responsive
web/static/js/main.js              → utilities JS
configs/nginx.conf                 → nginx reverse proxy
configs/desar.service              → systemd unit
Makefile                           → build, run, deploy
```

### Pendiente 🔲
```
internal/notify/notify.go          ✅ email SMTP + webhooks + templates HTML
internal/scheduler/scheduler.go    ✅ backup 3am + alertas vencimiento 8am + reporte lunes 7am
internal/sync/sync.go              ✅ sync bidireccional + notificaciones por sitio
web/handlers.go                    ✅ GET /reportes/csv export
go.sum                             → (se genera con go mod tidy)
```

---

## Arquitectura general

```
https://dominio.tld/           → landing page (Nginx sirve HTML estático)
https://dominio.tld/desar/     → panel admin web (Go puerto 8080 via Nginx)
https://dominio.tld/desar/ws   → WebSocket tiempo real
https://dominio.tld:8443/desar/api/v1/  → API para APK DESAR Android
```

Un solo binario Go escucha dos puertos:
- `:8080` → panel web HTML
- `:8443` → API REST para el APK

Nginx hace reverse proxy de HTTPS:443 → Go:8080 para el panel.
El APK conecta directo a dominio.tld:8443 con TLS.

---

## Base de datos

### admin.db (una sola, global)
```sql
companias       → id, nombre, api_key, plan, db_path, activo, fecha_vence
usuarios        → id, compania_id, email, password_hash, rol, activo
sesiones        → id, usuario_id, token, expira
auditoria       → id, compania_id, usuario_id, accion, detalle, ts
dispositivos    → id, compania_id, api_key, ultimo_sync
```

### {api_key}.db (una por compañía, en ./data/)
```sql
empleados       → espejo del APK DESAR
registros       → espejo del APK + sync_status
sitios          → espejo del APK
configuracion   → nombre_compania, hora_entrada, hora_salida, tolerancia_min
```

**sync_status en registros:** 0=pendiente, 1=sincronizado, 2=error

---

## Roles y permisos

| Rol         | Puede                                              |
|-------------|---------------------------------------------------|
| superadmin  | Todo, incluyendo crear/gestionar compañías         |
| admin       | Todo dentro de su compañía                         |
| gerente     | Ver empleados, todos los registros, reportes       |
| rrhh        | CRUD empleados, ver sitios                         |
| supervisor  | Solo ver registros y empleados (solo lectura)      |
| readonly    | Solo ver empleados y registros                     |

Matriz definida en `internal/auth/auth.go` función `permisos`.

---

## API endpoints (para el APK)

Todos requieren header `X-API-Key: desar_xxxxx`

```
GET  /desar/api/v1/ping              → verifica conexión
POST /desar/api/v1/sync              → batch sync registros + empleados
POST /desar/api/v1/registros         → registro individual
POST /desar/api/v1/empleados         → crear/actualizar empleado
GET  /desar/api/v1/empleados         → listar empleados
GET  /desar/api/v1/config            → config de la compañía
```

**Sync request del APK:**
```json
{
  "registros": [{ "codigo_empleado":"EMP001", "nombre_empleado":"Juan", 
    "tipo":"entrada", "timestamp":"2026-04-10T08:00:00", 
    "metodo":"rostro", "gps_lat":19.4, "gps_lon":-99.1 }],
  "empleados": [{ "codigo_empleado":"EMP001", "nombre":"Juan García", "activo":1 }]
}
```

---

## Panel web endpoints

Todos requieren cookie `desar_token` (JWT HttpOnly).

```
GET/POST /desar/login                → autenticación
GET      /desar/logout               → cerrar sesión
GET      /desar/                     → dashboard con stats + live feed
GET      /desar/ws                   → WebSocket tiempo real
GET      /desar/empleados            → lista empleados
GET      /desar/registros            → registros con filtros fecha/empleado
GET      /desar/registros/hoy        → JSON registros hoy (para AJAX)
GET      /desar/sitios               → lista sitios
GET/POST /desar/config               → configuración compañía
GET/POST /desar/usuarios             → gestión usuarios del panel
DELETE   /desar/usuarios/{id}        → desactivar usuario
GET      /desar/reportes             → exportar CSV

-- Solo superadmin --
GET      /desar/sa/companias         → lista todas las compañías
POST     /desar/sa/companias         → crear nueva compañía
GET      /desar/sa/companias/{id}    → detalle + API key
PUT      /desar/sa/companias/{id}/toggle → activar/pausar
```

---

## WebSocket - Eventos en tiempo real

El servidor hace broadcast a los clientes del panel cuando llega un registro del APK.

**Evento registro:**
```json
{
  "tipo": "registro",
  "compania_id": 1,
  "datos": {
    "codigo_empleado": "EMP001",
    "nombre_empleado": "Juan García",
    "tipo": "entrada",
    "timestamp": "2026-04-10T08:05:00",
    "sitio_trabajo": "Oficina Central",
    "metodo": "rostro"
  }
}
```

El dashboard JavaScript recibe esto y agrega la fila a la tabla sin recargar.
También actualiza los contadores de presentes/salidas vía AJAX.

---

## Configuración variables de entorno

```bash
API_PORT=8443          # Puerto API para el APK
WEB_PORT=8080          # Puerto panel web (Nginx hace proxy)
DBS_PATH=./data        # Directorio donde se crean las BDs SQLite
JWT_SECRET=xxxxx       # Secreto JWT mínimo 32 caracteres - CAMBIAR
```

---

## Instalación en servidor Linux

```bash
# 1. Compilar
make deps
make build

# 2. Copiar al servidor
make deploy SERVER=ubuntu@ip_servidor

# 3. Configurar Nginx
sudo cp configs/nginx.conf /etc/nginx/sites-available/desar
sudo ln -s /etc/nginx/sites-available/desar /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 4. Primer arranque - crea superadmin automáticamente
# Credenciales: admin@desar.local / admin123
# URL: https://dominio.tld/desar/

# 5. IMPORTANTE: cambiar password del superadmin al primer login
```

---

## Configurar APK DESAR para sincronizar

En el APK: Admin → Sync:
- **URL servidor:** `https://dominio.tld` (sin /api/v1)
- **Puerto:** `8443`
- **API Key:** el que muestra la pantalla de detalle de compañía en el superadmin

El APK construye la URL completa como: `{url}:{puerto}/desar/api/v1/{endpoint}`

---

## Módulos pendientes de implementar

### internal/notify/notify.go ✅ COMPLETADO
```go
// Enviar email SMTP cuando:
// - Empleado entra a sitio peligroso
// - Empleado con vencimiento próximo (< 30 días)
// - APK sin sincronizar > 24h
// - Nuevo registro de entrada/salida (configurable por compañía)

// Webhook: POST a URL configurable con payload JSON del evento
```

### internal/scheduler/scheduler.go ✅ COMPLETADO
```go
// Cada noche a las 3am:
// - Backup de cada BD de compañía a ./data/backups/
// - Retención 30 días (borrar backups viejos)
// - Reporte semanal por email (lunes 7am)
```

### internal/sync/sync.go ✅ COMPLETADO
```go
// Sync bidireccional:
// - Servidor puede mandar empleados nuevos/actualizados al APK
// - Response del /sync incluye empleados_nuevos[]
// - APK los importa si no los tiene
// Cola de mensajes si APK estuvo offline
```

### Reportes CSV ✅ COMPLETADO  |  PDF: pendiente
```go
// GET /desar/reportes/csv?desde=&hasta=&emp=
// Genera CSV de registros y fuerza descarga
// GET /desar/reportes/pdf → PDF con go-pdf o similar
```

---

## Dependencias Go

```
github.com/go-chi/chi/v5 v5.0.12
github.com/golang-jwt/jwt/v5 v5.2.1
github.com/gorilla/websocket v1.5.1
golang.org/x/crypto v0.22.0
modernc.org/sqlite v1.29.9
```

Para agregar email: `gopkg.in/mail.v2`  
Para PDF: `github.com/jung-kurt/gofpdf`

---

## Notas importantes

1. **SQLite con WAL mode** — cada BD usa WAL para mejor concurrencia lectura/escritura
2. **Sin CGO** — usa `modernc.org/sqlite` (puro Go), compila sin libsqlite3
3. **Templates embebidos** — los HTML van dentro del binario con `//go:embed`
4. **Private class `_` en Go** — los paquetes `internal/` no son importables desde fuera
5. **Un binario, dos puertos** — simplifica deploy, sin Docker necesario
6. **El panel arranca en /desar/** — la landing page de dominio.tld queda libre
