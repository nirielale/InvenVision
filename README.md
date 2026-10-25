# InvenVision

Sistema de gestión de inventario con detección de fechas de vencimiento mediante visión artificial (OpenCV + Tesseract OCR).

- **Backend:** Python, FastAPI, SQLAlchemy, JWT + bcrypt
- **Base de datos:** MySQL (`invenvision`)
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5, Chart.js (se sirve desde el mismo servidor FastAPI)
- **Estructura:** `backend/` (API), `frontend/` (interfaz), `ml/` (evaluación del OCR), `database/`, `docs/`

> **Estado:** prototipo. Lea [`docs/estado-y-limitaciones.md`](docs/estado-y-limitaciones.md) antes de usarlo: el OCR aún no se evaluó
> con fotos reales y la interfaz no se ha recorrido en un navegador.

## Requisitos (Windows)
1. Python 3.11+
2. MySQL en ejecución (servicio `MySQL93`, puerto 3306)
3. Tesseract OCR para Windows (necesario solo para escanear): `winget install UB-Mannheim.TesseractOCR`. El idioma español se toma de
   `ml/tessdata/spa.traineddata` (y `eng.traineddata`), que no se sube a Git; descárguelo con:
   ```powershell
   mkdir ml	essdata -Force
   Invoke-WebRequest https://github.com/tesseract-ocr/tessdata_fast/raw/main/spa.traineddata -OutFile ml	essdata\spa.traineddata
   Copy-Item "C:\Program Files\Tesseract-OCR	essdata\eng.traineddata" ml	essdata   ```
   (Alternativa: instalar el idioma Spanish con el instalador gráfico de UB-Mannheim.)
4. Para la cámara, abrir la aplicación desde `http://127.0.0.1:8000` o `localhost` (el navegador exige contexto seguro) y permitir el acceso.
5. Conexión a Internet en el navegador (Bootstrap, iconos y Chart.js se cargan desde CDN)

## Instalación
```powershell
cd Tesis_InvenVision
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
copy .env.example .env
notepad .env
```
En `.env` complete `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `JWT_SECRET` (genere uno con
`python -c "import secrets; print(secrets.token_hex(32))"`). Si Tesseract no está en el PATH, defina `TESSERACT_CMD`.
El archivo `.env` está en `.gitignore`: no se sube a Git.

## Base de datos
La base `invenvision` ya existe; **no se crea ni se recrea desde la aplicación**. Los modelos coinciden con el esquema real
(ver `docs/base-de-datos.md`). Compruébelo con `cd backend; python -m scripts.verificar_esquema` (solo lectura).
Se recomienda un usuario MySQL con permisos `SELECT, INSERT, UPDATE, DELETE` únicamente sobre `invenvision`.

## Crear un administrador (de forma segura)
```powershell
cd backend
python -m scripts.crear_admin
```
Pide nombre, correo y contraseña por teclado (sin eco). Solo inserta un usuario nuevo; si el correo existe, no modifica nada.

## Ejecutar
```powershell
cd backend
uvicorn app.main:app --reload
```
- Aplicación: http://127.0.0.1:8000
- Documentación Swagger: http://127.0.0.1:8000/docs

## Pruebas
```powershell
cd backend
python -m pytest -q
```
Las pruebas usan SQLite en memoria; **no tocan MySQL**. La prueba de OCR real se omite si Tesseract no está instalado.

## Datos de demostración (opcional)
```powershell
cd backend
python -m scripts.datos_demo --confirmar            # agrega productos con código DEMO-xxx
python -m scripts.datos_demo --confirmar --quitar   # quita solo los DEMO-xxx
```

## Guía de demostración
1. Inicie sesión con el administrador. 2. Revise **Categorías**. 3. Registre un producto con fecha de vencimiento cercana.
4. En **Escáner**, suba una foto de etiqueta (o use la cámara), revise las fechas candidatas, corrija si hace falta y confirme.
5. Compruebe **Alertas**, **Dashboard**, **Reportes** e **Historial**. 6. En **Perfil**, cambie los días de anticipación y observe cómo cambian los estados.

## Despliegue (Railway / Docker)
Hay `Dockerfile`, `.dockerignore` y `railway.json`. En producción (`ENVIRONMENT=production`) `JWT_SECRET` es obligatorio (mín. 32 caracteres),
no se publican `/docs` ni `/openapi.json` y el registro público queda deshabilitado salvo `ALLOW_REGISTRATION=true`. Las fotos y escaneos se
guardan en `UPLOAD_DIR` (por defecto `backend/uploads`; en Railway, un volumen). Guía completa: [`docs/despliegue-railway.md`](docs/despliegue-railway.md).
