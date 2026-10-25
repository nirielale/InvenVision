from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


class FakeDB:
    def __init__(self, fail=False):
        self.fail = fail

    def execute(self, *args, **kwargs):
        if self.fail:
            raise OperationalError("SELECT 1", {}, Exception("secreto"))


def override(fail):
    def _get_db():
        yield FakeDB(fail)

    return _get_db


def test_health_ok():
    app.dependency_overrides[get_db] = override(False)
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "connected"}


def test_health_db_caida_no_filtra_detalle():
    app.dependency_overrides[get_db] = override(True)
    r = TestClient(app).get("/health")
    assert r.status_code == 503
    assert "secreto" not in r.text
    app.dependency_overrides.clear()
