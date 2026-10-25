import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registra las tablas)
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Categoria, Usuario
from app.routers import common
from app.security import hash_password

PASSWORD = "Clave-de-prueba-1"


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Base SQLite en memoria, aislada por prueba. Nunca toca MySQL."""
    monkeypatch.setattr(settings, "jwt_secret", "secreto-solo-para-pruebas")
    monkeypatch.setattr(common, "UPLOAD_DIR", tmp_path)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False)
    s = Sesion()
    s.add_all([
        Usuario(nombre="Admin", email="admin@test.com", password_hash=hash_password(PASSWORD), rol="administrador"),
        Usuario(nombre="Operador", email="op@test.com", password_hash=hash_password(PASSWORD), rol="operador"),
        Categoria(nombre="Lácteos"),
        Categoria(nombre="Bebidas"),
    ])
    s.commit()

    def _get_db():
        d = Sesion()
        try:
            yield d
        finally:
            d.close()

    app.dependency_overrides[get_db] = _get_db
    yield s
    app.dependency_overrides.clear()
    s.close()


@pytest.fixture
def client(db):
    return TestClient(app)


def login(client, email):
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return login(client, "admin@test.com")


@pytest.fixture
def operador(client):
    return login(client, "op@test.com")
