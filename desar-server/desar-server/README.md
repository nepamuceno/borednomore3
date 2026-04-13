# DESAR Server v2.1

Panel de administración multicompañía para el sistema de control de asistencia DESAR.
Compatible con APK DESAR (Flutter) — sincronización bidireccional vía API REST + WebSocket.

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

## API APK — Endpoints `/desar/api/v1/`

Autenticación: Header `X-API-Key: <api_key_empresa>`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ping` | Estado del servidor |
| POST | `/sync` | Sync bidireccional (registros + empleados) |
| GET | `/registros?desde=&hasta=&empleado=` | Listar registros |
| POST | `/registros` | Crear registro individual |
| DELETE | `/registros/{id}` | Eliminar registro |
| GET | `/empleados` | Listar empleados |
| POST | `/empleados` | Crear/actualizar empleado |
| PUT | `/empleados/{codigo}` | Actualizar empleado completo |
| DELETE | `/empleados/{codigo}` | Dar de baja empleado |
| GET | `/jornadas?desde=&hasta=&empleado=` | Listar jornadas (APK recibe) |
| GET | `/sitios` | Listar sitios activos |
| POST | `/sitios` | Crear sitio |
| PUT | `/sitios/{id}` | Actualizar sitio |
| DELETE | `/sitios/{id}` | Desactivar sitio |
| GET | `/config` | Configuración de jornada para APK |

## Modelo de Sync (`POST /sync`)

```json
{
  "registros": [
    {
      "empleado_id": 1,
      "codigo_empleado": "EMP001",
      "nombre_empleado": "Juan Pérez",
      "tipo": "entrada",
      "timestamp": "2026-04-13T08:05:00",
      "gps_lat": 19.4326,
      "gps_lon": -99.1332,
      "sitio_trabajo": "Planta Principal",
      "metodo": "qr",
      "notas": ""
    }
  ],
  "empleados": [],
  "version": "0.0.1-beta"
}
```

**Respuesta:**
```json
{
  "ok": true,
  "registros_sincronizados": 1,
  "empleados_sincronizados": 0,
  "empleados_nuevos": [],
  "timestamp": "2026-04-13T08:05:01Z"
}
```

`empleados_nuevos` contiene empleados creados en el servidor que el APK aún no tiene (sync_status=0).

## Notificaciones aisladas por empresa

- WebSocket (`/desar/ws`): solo recibe eventos de su propia compañía
- Sync: cada APK se identifica con `X-API-Key` — servidor registra dispositivo automáticamente
- Cambios en empleados hechos en el panel web: el APK los recibe en su próximo sync via `empleados_nuevos`

## Reportes Web

### Excel/CSV
- `/reportes/excel?tipo=asistencias&desde=&hasta=`
- `/reportes/excel?tipo=empleados`
- `/reportes/excel/tardanzas?desde=&hasta=`
- `/reportes/excel/registros?desde=&hasta=&empleado=`
- `/reportes/excel/catalogo?tipo=gafetes`
- `/reportes/excel/catalogo?tipo=qr`
- `/reportes/csv?desde=&hasta=`

### PDF
- `/pdf/nomina?desde=&hasta=`
- `/pdf/registros?desde=&hasta=`
- `/pdf/tardanzas?desde=&hasta=`
- `/pdf/vigencias`
- `/pdf/gafetes`
- `/pdf/catalogo-qr`

## Configuración desde el panel

La página `/desar/config` cubre todos los campos del APK:
- Datos de empresa (nombre, RFC, dirección, etc.)
- Jornada (hora entrada/salida, tolerancia, horas, umbral facial)
- Zona horaria
- Bot Telegram (token, chat ID)
- WhatsApp Business API (URL, token, phone ID, verify token)
- Facebook Messenger (page token, app ID/secret)
- Prefijo de comandos bot
- Formato de reporte por defecto

Ver `diseño.md` para documentación completa de arquitectura.
