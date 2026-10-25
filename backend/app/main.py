from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import ROOT_DIR, Settings, settings
from app.database import get_db
from app.routers import auth, categories, common, products, reports, scan, users


def _verificar_carpeta_subidas() -> None:
    """En producción la carpeta de subidas debe existir y poder escribirse (p. ej. un volumen montado)."""
    carpeta = common.UPLOAD_DIR
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        prueba = carpeta / ".escritura"
        prueba.write_bytes(b"")
        prueba.unlink()
    except OSError as e:
        raise RuntimeError(
            f"UPLOAD_DIR ({carpeta}) no se puede escribir: {e.strerror or e}. "
            "Revise que el volumen esté montado y que el proceso tenga permisos."
        ) from e


def crear_app(cfg: Settings = settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        cfg.verificar_produccion()  # RuntimeError con mensaje claro: el servidor no arranca
        if cfg.es_produccion:
            _verificar_carpeta_subidas()
        yield

    # En producción no se publican /docs, /redoc ni /openapi.json
    docs = {} if not cfg.es_produccion else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(
        title="InvenVision API",
        version="0.2.0",
        description="Gestión de inventario y detección de fechas de vencimiento con visión artificial.",
        lifespan=lifespan,
        **docs,
    )

    app.state.settings = cfg
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

    @app.get("/api/config", tags=["Sistema"])
    def configuracion_publica():
        """Opciones públicas que necesita la interfaz antes de iniciar sesión. No incluye secretos."""
        return {"registro_habilitado": cfg.registro_habilitado}

    # El frontend se sirve desde el mismo origen (después de las rutas /api)
    frontend = ROOT_DIR / "frontend"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


app = crear_app()
