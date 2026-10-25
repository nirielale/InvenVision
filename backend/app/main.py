from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import ROOT_DIR
from app.database import get_db
from app.routers import auth, categories, products, reports, scan, users

app = FastAPI(
    title="InvenVision API",
    version="0.2.0",
    description="Gestión de inventario y detección de fechas de vencimiento con visión artificial.",
)

for modulo in (auth, users, categories, products, scan, reports):
    app.include_router(modulo.router)


@app.get("/api/health", tags=["Sistema"])
def health(db: Session = Depends(get_db)):
    """Comprueba que la API responde y que la conexión con MySQL funciona."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # No se devuelve el detalle del error para no exponer datos de conexión
        raise HTTPException(status_code=503, detail="No se pudo conectar con la base de datos")
    return {"status": "ok", "database": "connected"}


# El frontend se sirve desde el mismo origen (después de las rutas /api)
_frontend = ROOT_DIR / "frontend"
if _frontend.is_dir():
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")
