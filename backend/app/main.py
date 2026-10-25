from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db

app = FastAPI(title="InvenVision API", version="0.1.0")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Comprueba que la API responde y que la conexión con MySQL funciona."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # No se devuelve el detalle del error para no exponer datos de conexión
        raise HTTPException(status_code=503, detail="No se pudo conectar con la base de datos")
    return {"status": "ok", "database": "connected"}
