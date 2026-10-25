# Despliegue en Railway

> Estado: **preparado, no publicado ni probado en Railway**. La imagen Docker no se pudo construir en el equipo de desarrollo
> (no hay Docker). Las comprobaciones hechas y las pendientes están en [`estado-y-limitaciones.md`](estado-y-limitaciones.md).

## Qué se despliega
El `Dockerfile` (raíz del repositorio) construye una imagen con Python 3.11, FastAPI, OpenCV y Tesseract con **español e inglés**
(paquetes Debian `tesseract-ocr-spa` y `tesseract-ocr-eng`; el build falla si falta alguno). La API sirve también el frontend.
`railway.json` indica usar ese Dockerfile y `/api/health` como health check. El arranque usa `0.0.0.0` y el puerto `PORT` que define Railway.
La imagen **no** incluye `.env`, `database/`, respaldos `.sql`, PDFs, `ml/`, pruebas ni `backend/uploads` (ver `.dockerignore`).

## Variables del servicio (Railway → Variables)
| Variable | Valor |
|---|---|
| `JWT_SECRET` | Obligatoria, mínimo 32 caracteres. Genere una con `python -c "import secrets; print(secrets.token_hex(32))"` y péguela solo en Railway. Sin ella (o si es corta) el servidor **no arranca** y lo explica en el log. |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Datos de la base MySQL (p. ej. referencias al servicio MySQL de Railway, como `${{MySQL.MYSQLHOST}}`; compruebe los nombres exactos en su panel). |
| `ENVIRONMENT` | `production` (la imagen ya lo trae por defecto). En producción no hay `/docs`, `/redoc` ni `/openapi.json`. |
| `ALLOW_REGISTRATION` | Omitida/`false` en producción: el registro público devuelve 403 (el inicio de sesión sigue funcionando y un administrador puede crear usuarios). `true` solo si desea registro abierto. |
| `UPLOAD_DIR` | `/data/uploads` (valor por defecto de la imagen); debe estar en un volumen persistente. |

No suba ningún valor secreto a Git. `.env.example` solo documenta los nombres.

## Volumen persistente (fotos y escaneos)
El disco del contenedor es efímero: sin volumen, las imágenes se pierden en cada despliegue y el historial queda apuntando a archivos inexistentes.
1. En el servicio: **Settings → Volumes → Add Volume**, con *Mount path* `/data`.
2. Deje `UPLOAD_DIR=/data/uploads`.
3. El contenedor corre con un usuario sin privilegios. Si el log indica `UPLOAD_DIR (...) no se puede escribir`, defina la variable
   `RAILWAY_RUN_UID=0` (los volúmenes se montan como root; verifíquelo en la documentación de Railway).
Para uso local no cambia nada: sin `UPLOAD_DIR` se usa `backend/uploads`. Las imágenes existentes no se mueven ni se borran.

## Base de datos
1. Añada un servicio MySQL al proyecto.
2. Importe `database/invenvision_backup_compartible.sql` con un usuario con permisos para crear la base (el script crea `invenvision`
   y hace `DROP TABLE IF EXISTS`; úselo solo sobre una base vacía). Pasos de Workbench en [`restaurar-base-de-datos.md`](restaurar-base-de-datos.md),
   conectándose por el host/puerto públicos del servicio MySQL.
3. Use `DB_NAME=invenvision` en el servicio de la API.
4. **Cambie de inmediato la contraseña del usuario demo** (su clave la conoce quien recibió el respaldo). Desde su equipo, con las variables
   `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` definidas solo en esa sesión de PowerShell (tienen prioridad sobre `.env`):
   `cd backend; python -m scripts.restablecer_password`.

## Antes de abrirlo a usuarios reales
- Sin límite de intentos de inicio de sesión (fuerza bruta) ni cabeceras de seguridad adicionales.
- El OCR consume CPU y memoria; elija un plan con margen y pruebe con fotos reales.
- Bootstrap, iconos y Chart.js se cargan desde CDN.
