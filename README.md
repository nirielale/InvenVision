# InvenVision

Sistema inteligente de gestión de inventario y detección de productos próximos a vencer mediante visión artificial.

## Estructura
- `backend/`: API FastAPI
- `database/`: esquema SQL de MySQL
- `frontend/`: interfaz web (HTML, CSS, JS, Bootstrap)
- `ml/`: visión artificial (OpenCV + OCR)
- `docs/`: documentación

## Puesta en marcha (backend)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
copy .env.example .env   # y completar credenciales
```
