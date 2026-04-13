# DESAR Server — Documento de Diseño Completo
> Versión 2.0 — PostgreSQL/SQLite dual, roles CRUD completo, PDF integrado.

---

## Estado del código ✅

```
go.mod                                      ✅ sqlite + postgres + gofpdf + lib/pq
internal/models/models.go                   ✅ todos los structs APK + sync
internal/db/manager.go                      ✅ dual SQLite/PostgreSQL, pool por compañía
internal/auth/auth.go                       ✅ JWT, bcrypt, roles, permisos granulares
internal/ws/hub.go                          ✅ WebSocket hub tiempo real
internal/pdf/pdf.go                         ✅ nómina, gafetes CR80, vigencias
internal/api/v1/handlers.go                 ✅ endpoints APK
internal/web/handlers.go                    ✅ panel web CRUD completo con permisos por rol
internal/sync/sync.go                       ✅ sync bidireccional todos los campos
internal/notify/notify.go                   ✅ email SMTP + webhooks + templates HTML
internal/scheduler/scheduler.go             ✅ backups 3am + alertas 8am + reporte lunes 7am
web/templates/auth/login.html               ✅
web/templates/auth/registro.html            ✅ auto-registro nueva empresa
web/templates/admin/dashboard.html          ✅ WebSocket live
web/templates/admin/empleados.html          ✅ búsqueda + eliminar por rol
web/templates/admin/registros.html          ✅ filtros + eliminar por rol
web/templates/admin/sitios.html             ✅
web/templates/admin/config.html             ✅
web/templates/admin/usuarios.html           ✅ crear/editar/desactivar + tabla de roles
web/templates/admin/reportes.html           ✅ CSV, Excel, PDF (nómina, gafetes, vigencias)
web/templates/admin/reporte_tipo.html       ✅
web/templates/superadmin/companias.html     ✅ CRUD compañías
web/templates/superadmin/compania_detalle.html ✅ editar + nav usuarios/empleados/registros
web/templates/superadmin/compania_usuarios.html ✅ CRUD usuarios por compañía (SA)
web/templates/superadmin/compania_empleados.html ✅
web/templates/superadmin/compania_registros.html ✅
web/static/css/main.css                     ✅ responsive + badge-rol por color
web/static/js/main.js                       ✅ delete/toggle con confirm + date defaults
configs/nginx.conf                          ✅
configs/desar.service                       ✅
Makefile                                    ✅
```

---

## Arquitectura

```
https://dominio.tld/desar/       → panel admin web  (Go :8080 via Nginx)
https://dominio.tld/desar/ws     → WebSocket tiempo real
https://dominio.tld:8443/desar/api/v1/  → API para APK Android
```

Un solo binario Go escucha dos puertos:
- `:8080` → panel web HTML/template
- `:8443` → API REST APK

---

## Motor de base de datos — opción en configuración

### SQLite (default, desarrollo)
```bash
DB_MODE=sqlite      # default
DBS_PATH=./data     # directorio de archivos .db
```
- `data/admin.db` — usuarios, compañías, sesiones, auditoría
- `data/company_<suffix>.db` — una por compañía (empleados, registros, sitios, config, jornadas)

### PostgreSQL (producción)
```bash
DB_MODE=postgres
DB_ADMIN_DSN=postgres://user:pass@host/desar_admin
DB_DSN_BASE=postgres://user:pass@host/
```
- BD admin: `desar_admin`
- BD por compañía: `desar_company_<suffix>` (nombre = `db_path` en la tabla companias)

**Nota:** modernc/sqlite acepta `$1` igual que `?`, por lo que todos los queries usan `$N` y funcionan en ambos motores sin cambios.

---

## Roles y permisos

| Rol         | Permisos                                                                    |
|-------------|-----------------------------------------------------------------------------|
| **superadmin** | `*` — todo el sistema, todas las compañías                               |
| **admin**   | empleados.* · registros.* · sitios.* · reportes.* · usuarios.* · config.* · pdf.* |
| **gerente** | empleados.ver · registros.ver/editar · sitios.ver · reportes.* · pdf.*     |
| **rrhh**    | empleados.* · sitios.ver · reportes.ver · pdf.ver                          |
| **supervisor** | registros.ver · empleados.ver                                           |
| **readonly** | empleados.ver · registros.ver                                              |

### Reglas de asignación de roles
- Un usuario solo puede asignar roles **iguales o inferiores** al suyo
- `superadmin` puede asignar cualquier rol (excepto crear otro superadmin desde el panel de compañía normal)
- `admin` puede asignar: admin, gerente, rrhh, supervisor, readonly
- `gerente` puede asignar: gerente, rrhh, supervisor, readonly
- `rrhh`/`supervisor`/`readonly` no pueden gestionar usuarios

---

## Multicompañía

Cada compañía tiene:
- Su propia BD aislada (SQLite: archivo separado; PostgreSQL: base de datos separada)
- Sus propios empleados, registros, sitios, configuración, jornadas
- Sus propios usuarios del panel (admin, gerente, rrhh, supervisor, readonly)
- Su propia API Key para el APK
- Su propio plan (basico: 25 emp / estandar / enterprise: ilimitado)

El superadmin ve y gestiona **todas** las compañías desde `/desar/sa/companias`.

---

## PDF — librería gofpdf

Tres reportes PDF implementados en `internal/pdf/pdf.go`:

### Nómina (`GET /desar/pdf/nomina?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`)
- Hoja apaisada tipo carta
- Columnas: código, nombre, puesto, días laborados, horas trabajadas, salario/día, bruto, descuentos, neto
- Totales al pie con fondo azul
- Salario base configurable (actualmente 200 MXN/día como placeholder)
- Descuentos estimados 12% (IMSS + ISR simplificado)

### Gafetes CR80 (`GET /desar/pdf/gafetes`)
- Tamaño real tarjeta de crédito (85.6×54mm)
- 2 columnas por página A4 vertical
- Diseño: fondo azul DESAR, código grande, nombre, puesto, sitio, datos QR en texto
- Requiere `pdf.ver` (admin, gerente, rrhh)

### Vigencias (`GET /desar/pdf/vigencias`)
- Lista todos los empleados activos con fecha de vencimiento
- Estado: VIGENTE (verde) / POR VENCER ≤30 días (naranja) / VENCIDO (rojo)
- Ordenado por fecha de vencimiento ascendente

### 🚧 Próximamente
- Catálogo QR (código QR real con librería qr)
- Envío automático por email (scheduler ya preparado)
- Horas extras
- Reporte de tardanzas en PDF

---

## Variables de entorno

```bash
# Puerto
API_PORT=8443           # API APK (default 8443)
WEB_PORT=8080           # Panel web (default 8080)

# Base de datos
DB_MODE=sqlite          # sqlite | postgres
DBS_PATH=./data         # ruta archivos SQLite
DB_ADMIN_DSN=...        # PostgreSQL admin DSN
DB_DSN_BASE=...         # PostgreSQL base DSN (sin dbname)

# JWT
JWT_SECRET=cambia-esto  # mínimo 32 caracteres

# SMTP (notificaciones)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu@email.com
SMTP_PASSWORD=xxx
SMTP_FROM=noreply@tudominio.com

# HTTPS automático (si usas nginx con SSL)
FORCE_HTTPS=1           # fuerza cookie Secure=true
```

---

## Instalación

```bash
# Desarrollo local (SQLite)
make run
# → http://localhost:8080/desar/
# → admin@desar.local / admin123

# Compilar
make build

# PostgreSQL producción
export DB_MODE=postgres
export DB_ADMIN_DSN="postgres://desar:password@localhost/desar_admin"
export DB_DSN_BASE="postgres://desar:password@localhost/"
createdb desar_admin
./desar-server

# Deploy
make deploy SERVER=usuario@ip
```

---

## Dependencias Go

```
github.com/go-chi/chi/v5 v5.0.12
github.com/golang-jwt/jwt/v5 v5.2.1
github.com/gorilla/websocket v1.5.1
github.com/jung-kurt/gofpdf v1.16.2
github.com/lib/pq v1.10.9
golang.org/x/crypto v0.22.0
modernc.org/sqlite v1.29.9
```

---

## Rutas web completas

```
GET  /desar/login                          Login
POST /desar/login
GET  /desar/logout
GET  /desar/registro                       Auto-registro nueva compañía
POST /desar/registro

GET  /desar/                               Dashboard
GET  /desar/ws                             WebSocket
GET  /desar/empleados                      Lista empleados
DELETE /desar/empleados/{id}               Eliminar (requiere empleados.eliminar)
GET  /desar/registros                      Lista registros con filtros
GET  /desar/registros/hoy                  JSON registros hoy (WebSocket)
DELETE /desar/registros/{id}               Eliminar (requiere registros.eliminar)
GET  /desar/sitios                         Lista sitios
GET  /desar/config                         Configuración (requiere config.ver)
POST /desar/config                         Guardar config (requiere config.editar)
GET  /desar/usuarios                       Gestión usuarios (requiere usuarios.ver)
POST /desar/usuarios                       Crear usuario (requiere usuarios.crear)
POST /desar/usuarios/{id}/editar           Editar usuario (requiere usuarios.editar)
DELETE /desar/usuarios/{id}                Desactivar (requiere usuarios.eliminar)
POST /desar/usuarios/{id}/password         Cambiar password
GET  /desar/reportes                       Panel reportes
GET  /desar/reportes/csv                   Exportar CSV
GET  /desar/reportes/excel                 Exportar Excel (tipo=asistencias|empleados|tardanzas)
GET  /desar/pdf/nomina                     PDF Nómina (requiere pdf.ver)
GET  /desar/pdf/gafetes                    PDF Gafetes CR80 (requiere pdf.ver)
GET  /desar/pdf/vigencias                  PDF Vigencias (requiere pdf.ver)

# Superadmin
GET  /desar/sa/companias                   Lista todas las compañías
POST /desar/sa/companias                   Crear compañía
GET  /desar/sa/companias/{id}              Detalle + editar compañía
POST /desar/sa/companias/{id}/editar       Guardar edición
PUT  /desar/sa/companias/{id}/toggle       Activar/Pausar
DELETE /desar/sa/companias/{id}            Desactivar
GET  /desar/sa/companias/{id}/empleados    Ver empleados
GET  /desar/sa/companias/{id}/registros    Ver registros
GET  /desar/sa/companias/{id}/usuarios     Gestionar usuarios
POST /desar/sa/companias/{id}/usuarios     Crear usuario
DELETE /desar/sa/companias/{id}/usuarios/{uid}  Desactivar usuario
DELETE /desar/sa/registros/{id}            Eliminar registro
DELETE /desar/sa/empleados/{id}            Eliminar empleado

# API APK
POST /desar/api/v1/sync                    Sync bidireccional
GET  /desar/api/v1/ping
POST /desar/api/v1/empleados
GET  /desar/api/v1/empleados
PUT  /desar/api/v1/empleados/{id}
DELETE /desar/api/v1/empleados/{id}
POST /desar/api/v1/registros
GET  /desar/api/v1/registros
```

---

## Notas de migración desde v1

1. Las queries usan `$1` en lugar de `?` — modernc/sqlite lo acepta igual
2. `db_path` en PostgreSQL es el **nombre de la base de datos** (no un path de archivo)
3. `NewCompanyDBPath()` genera automáticamente el path/nombre correcto según el motor
4. Eliminar `data/admin.db` y `data/company_*.db` para recrear el schema limpio en desarrollo
