"""Pruebas de la configuración de despliegue (producción / Railway)."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import ROOT_DIR, Settings
from app.main import app as app_global
from app.main import crear_app
from app.routers import common
from app.services import vision
from tests.conftest import PASSWORD

SECRETO = "s" * 40


def cfg(**kw) -> Settings:
    """Configuración aislada: no lee el .env real ni depende del entorno del equipo."""
    base = dict(environment="development", jwt_secret=SECRETO, db_user="usuario")
    base.update(kw)
    return Settings(_env_file=None, **base)


def app_con(cfg_, db):
    """App nueva con la misma base de pruebas (SQLite) que usa el resto de la suite."""
    a = crear_app(cfg_)
    a.dependency_overrides.update(app_global.dependency_overrides)
    return a


NUEVO = {"nombre": "Ana", "email": "ana@test.com", "password": "Otra-clave-123"}


# ---------- JWT_SECRET y arranque ----------
@pytest.mark.parametrize("secreto", ["", "corto", "x" * 31])
def test_produccion_sin_jwt_secret_valido_no_arranca(db, secreto):
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        with TestClient(app_con(cfg(environment="production", jwt_secret=secreto), db)):
            pass


def test_produccion_sin_usuario_de_bd_no_arranca(db):
    with pytest.raises(RuntimeError, match="DB_USER"):
        with TestClient(app_con(cfg(environment="production", db_user=""), db)):
            pass


def test_produccion_valida_arranca_y_health_responde(db, tmp_path, monkeypatch):
    monkeypatch.setattr(common, "UPLOAD_DIR", tmp_path / "volumen" / "uploads")
    with TestClient(app_con(cfg(environment="production"), db)) as c:
        assert c.get("/api/health").json() == {"status": "ok", "database": "connected"}
    assert (tmp_path / "volumen" / "uploads").is_dir()  # se crea en el volumen


def test_desarrollo_arranca_sin_jwt_secret(db):
    with TestClient(app_con(cfg(jwt_secret=""), db)) as c:
        assert c.get("/api/health").status_code == 200


def test_produccion_con_carpeta_de_subidas_no_escribible_no_arranca(db, tmp_path, monkeypatch):
    archivo = tmp_path / "es-un-archivo"
    archivo.write_text("x")
    monkeypatch.setattr(common, "UPLOAD_DIR", archivo / "uploads")  # no se puede crear dentro de un archivo
    with pytest.raises(RuntimeError, match="UPLOAD_DIR"):
        with TestClient(app_con(cfg(environment="production"), db)):
            pass


def test_el_mensaje_de_error_no_incluye_el_secreto(db):
    with pytest.raises(RuntimeError) as e:
        with TestClient(app_con(cfg(environment="production", jwt_secret="corto-secreto"), db)):
            pass
    assert "corto-secreto" not in str(e.value)


# ---------- documentación de la API ----------
RUTAS_DOCS = ("/docs", "/redoc", "/openapi.json")


def test_documentacion_deshabilitada_en_produccion(db, tmp_path, monkeypatch):
    monkeypatch.setattr(common, "UPLOAD_DIR", tmp_path)
    with TestClient(app_con(cfg(environment="production"), db)) as c:
        for ruta in RUTAS_DOCS:
            assert c.get(ruta).status_code == 404, ruta
        assert c.get("/api/health").status_code == 200  # el resto sigue disponible


def test_documentacion_disponible_en_desarrollo(db):
    with TestClient(app_con(cfg(), db)) as c:
        for ruta in RUTAS_DOCS:
            assert c.get(ruta).status_code == 200, ruta


# ---------- registro público ----------
def test_registro_habilitado_por_defecto_en_desarrollo(db):
    c = TestClient(app_con(cfg(), db))
    assert c.get("/api/config").json() == {"registro_habilitado": True}
    assert c.post("/api/auth/register", json=NUEVO).status_code == 201


def test_registro_deshabilitado_por_defecto_en_produccion_pero_login_funciona(db, tmp_path, monkeypatch):
    monkeypatch.setattr(common, "UPLOAD_DIR", tmp_path)
    with TestClient(app_con(cfg(environment="production"), db)) as c:
        assert c.get("/api/config").json() == {"registro_habilitado": False}
        r = c.post("/api/auth/register", json=NUEVO)
        assert r.status_code == 403 and "deshabilitado" in r.json()["detail"]
        login = c.post("/api/auth/login", json={"email": "admin@test.com", "password": PASSWORD})
        assert login.status_code == 200
        # el administrador sigue pudiendo crear usuarios
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert c.post("/api/usuarios", json=NUEVO, headers=h).status_code == 201


def test_registro_se_puede_habilitar_en_produccion_y_deshabilitar_en_desarrollo(db, tmp_path, monkeypatch):
    monkeypatch.setattr(common, "UPLOAD_DIR", tmp_path)
    with TestClient(app_con(cfg(environment="production", allow_registration=True), db)) as c:
        assert c.post("/api/auth/register", json=NUEVO).status_code == 201
    c = TestClient(app_con(cfg(allow_registration=False), db))
    assert c.post("/api/auth/register", json={**NUEVO, "email": "otra@test.com"}).status_code == 403


def test_variables_de_entorno_se_interpretan(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ALLOW_REGISTRATION", "false")
    monkeypatch.setenv("UPLOAD_DIR", "")  # vacío se ignora
    s = Settings(_env_file=None)
    assert s.es_produccion and s.registro_habilitado is False and s.upload_dir == ""
    monkeypatch.setenv("ALLOW_REGISTRATION", "true")
    assert Settings(_env_file=None).registro_habilitado is True


# ---------- UPLOAD_DIR ----------
def test_upload_dir_por_defecto_es_backend_uploads():
    assert Settings(_env_file=None).upload_path == ROOT_DIR / "backend" / "uploads"


def test_upload_dir_configurable_absoluta_y_relativa(tmp_path, monkeypatch):
    assert Settings(_env_file=None, upload_dir=str(tmp_path / "vol")).upload_path == (tmp_path / "vol").resolve()
    monkeypatch.chdir(tmp_path)
    assert Settings(_env_file=None, upload_dir="datos").upload_path == (tmp_path / "datos").resolve()


def test_guardar_y_leer_archivos_en_la_carpeta_configurada(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "UPLOAD_DIR", tmp_path / "volumen")
    ruta = common.guardar_archivo("scans", "a.jpg", b"datos")
    assert ruta == "scans/a.jpg"
    assert (tmp_path / "volumen" / "scans" / "a.jpg").read_bytes() == b"datos"
    assert common.ruta_archivo(ruta) is not None
    assert common.ruta_archivo("../../etc/passwd") is None  # no se sale de la carpeta


# ---------- idiomas de Tesseract (simulando la instalación de Linux) ----------
@pytest.fixture
def tesseract_linux(monkeypatch, tmp_path):
    """Tesseract en /usr/bin (sin carpeta tessdata junto al ejecutable, como en Debian)."""
    monkeypatch.setattr(vision, "_localizar_tesseract", lambda: "/usr/bin/tesseract")
    monkeypatch.setattr(vision, "TESSDATA_LOCAL", tmp_path / "sin-datos-locales")
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)
    vision._listar_idiomas.cache_clear()
    yield
    vision._listar_idiomas.cache_clear()


@pytest.mark.parametrize("instalados, esperado", [
    (["eng", "osd", "spa"], "spa+eng"),
    (["spa", "eng"], "spa+eng"),
    (["eng", "osd"], "eng"),
    (["spa"], "spa"),
    ([], "eng"),
])
def test_idiomas_se_detectan_con_la_instalacion_del_sistema(tesseract_linux, monkeypatch, instalados, esperado):
    import pytesseract

    monkeypatch.setattr(pytesseract, "get_languages", lambda config="": instalados)
    assert vision._idiomas() == esperado


def test_idiomas_si_tesseract_falla_usa_ingles(tesseract_linux, monkeypatch):
    import pytesseract

    def falla(config=""):
        raise RuntimeError("tesseract roto")

    monkeypatch.setattr(pytesseract, "get_languages", falla)
    assert vision._idiomas() == "eng"


def test_idiomas_se_consultan_una_sola_vez(tesseract_linux, monkeypatch):
    import pytesseract

    llamadas = []
    monkeypatch.setattr(pytesseract, "get_languages", lambda config="": llamadas.append(1) or ["eng", "spa"])
    for _ in range(5):
        vision._idiomas()
    assert len(llamadas) == 1


def test_estado_ocr_informa_idiomas_y_faltantes(client, operador, tesseract_linux, monkeypatch):
    import pytesseract

    monkeypatch.setattr(pytesseract, "get_languages", lambda config="": ["eng", "osd"])
    r = client.get("/api/ocr/estado", headers=operador).json()
    assert r == {"disponible": True, "idiomas": ["eng"], "idiomas_faltantes": ["spa"]}


@pytest.mark.skipif(not vision.ocr_disponible(), reason="Tesseract no está instalado en este equipo")
def test_tesseract_real_tiene_espanol_e_ingles():
    vision._listar_idiomas.cache_clear()
    assert {"spa", "eng"} <= set(vision.idiomas_instalados())
    assert vision._idiomas() == "spa+eng"


# ---------- archivos de despliegue (comprobaciones estáticas) ----------
def _leer(ruta: str) -> str:
    return (ROOT_DIR / ruta).read_text(encoding="utf-8")


def test_dockerfile_arranca_en_0000_con_el_puerto_de_railway_y_tesseract():
    d = _leer("Dockerfile")
    assert "--host 0.0.0.0" in d and "${PORT:-8000}" in d
    assert "FROM python:3.11" in d
    for paquete in ("tesseract-ocr ", "tesseract-ocr-spa", "tesseract-ocr-eng"):
        assert paquete in d
    assert "ENVIRONMENT=production" in d and "UPLOAD_DIR=/data/uploads" in d
    assert "--reload" not in d and "USER appuser" in d


def test_dockerfile_no_copia_secretos_ni_todo_el_contexto():
    copias = [l.split()[1] for l in _leer("Dockerfile").splitlines() if l.startswith("COPY ")]
    assert copias and "." not in copias  # nada de `COPY . .`
    assert not any(".env" in c or c.startswith(("database", "docs", "ml")) for c in copias)
    assert not any(k in _leer("Dockerfile") for k in ("JWT_SECRET=", "DB_PASSWORD=", "DB_USER="))


def test_dockerignore_excluye_datos_personales_y_secretos():
    lineas = {l.strip() for l in _leer(".dockerignore").splitlines() if l.strip() and not l.startswith("#")}
    for esperado in (".env", "**/.env", "database", "**/*.sql", "*.pdf", "venv", "backend/uploads",
                     "backend/tests", "ml", "**/__pycache__", "**/.pytest_cache", ".git"):
        assert esperado in lineas, esperado


def test_lo_que_copia_el_dockerfile_no_contiene_archivos_sensibles():
    """Recorre las carpetas realmente copiadas por el Dockerfile y busca archivos que no deben entrar."""
    copias = [l.split()[1] for l in _leer("Dockerfile").splitlines() if l.startswith("COPY ")]
    prohibido = (".env", ".sql", ".pdf", ".traineddata", ".db", ".sqlite")
    encontrados = []
    for c in copias:
        base = ROOT_DIR / c
        for f in ([base] if base.is_file() else base.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and (f.name == ".env" or f.suffix.lower() in prohibido):
                encontrados.append(str(f.relative_to(ROOT_DIR)))
    assert encontrados == []


def test_railway_json_usa_dockerfile_y_health_check():
    r = json.loads(_leer("railway.json"))
    assert r["build"]["builder"] == "DOCKERFILE"
    assert r["deploy"]["healthcheckPath"] == "/api/health"


def test_requirements_de_produccion_no_incluyen_herramientas_de_prueba():
    prod = _leer("backend/requirements.txt").lower()
    assert "pytest" not in prod and "httpx" not in prod
    assert "pytesseract" in prod and "opencv-python-headless" in prod
    dev = _leer("backend/requirements-dev.txt")
    assert "-r requirements.txt" in dev and "pytest" in dev


def test_env_example_no_contiene_secretos_y_documenta_las_variables():
    e = _leer(".env.example")
    for var in ("ENVIRONMENT=", "UPLOAD_DIR=", "ALLOW_REGISTRATION", "JWT_SECRET="):
        assert var in e
    valores = {l.split("=", 1)[0]: l.split("=", 1)[1].strip() for l in e.splitlines() if "=" in l and not l.startswith("#")}
    assert valores["JWT_SECRET"] == "" and valores["DB_PASSWORD"] == "" and valores["DB_USER"] == ""
    Settings(_env_file=None)  # las líneas vacías del ejemplo no rompen la configuración
