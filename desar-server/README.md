# DESAR Server v2.0

Panel de administración multicompañía para el sistema de control de asistencia DESAR.

## Inicio rápido

```bash
# 1. Instalar dependencias
make tidy

# 2. Correr en modo desarrollo (SQLite, auto-crea superadmin)
make run

# 3. Abrir panel
http://localhost:8080/desar/
# Usuario: admin@desar.local  |  Password: admin123
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DB_MODE` | `sqlite` | `sqlite` o `postgres` |
| `DBS_PATH` | `./data` | Directorio de archivos SQLite |
| `DB_ADMIN_DSN` | — | DSN PostgreSQL BD admin |
| `DB_DSN_BASE` | — | DSN base PostgreSQL (sin dbname) |
| `API_PORT` | `8443` | Puerto API APK |
| `WEB_PORT` | `8080` | Puerto panel web |
| `JWT_SECRET` | — | Secreto JWT (mínimo 32 chars) |
| `SMTP_HOST` | — | Host SMTP para notificaciones |
| `FORCE_HTTPS` | `0` | `1` para forzar cookie Secure |

## PostgreSQL

```bash
createdb desar_admin
export DB_MODE=postgres
export DB_ADMIN_DSN="postgres://user:pass@localhost/desar_admin"
export DB_DSN_BASE="postgres://user:pass@localhost/"
make run
```

## Roles

| Rol | Acceso |
|-----|--------|
| `superadmin` | Todo el sistema, todas las compañías |
| `admin` | Todo en su compañía |
| `gerente` | Ver empleados, registros, reportes, PDF |
| `rrhh` | CRUD empleados, reportes básicos |
| `supervisor` | Solo ver registros y empleados |
| `readonly` | Solo lectura |

## PDF Reports

- `GET /desar/pdf/nomina?desde=YYYY-MM-DD&hasta=YYYY-MM-DD` — Nómina
- `GET /desar/pdf/gafetes` — Catálogo gafetes CR80
- `GET /desar/pdf/vigencias` — Reporte de vigencias de contratos

Ver `diseño.md` para documentación completa.
