from datetime import date, timedelta

import cv2
import numpy as np

from app.services import vision
from tests.conftest import PASSWORD


def producto(cod="COD-1", dias=30, **extra):
    datos = {
        "nombre": f"Producto {cod}", "codigo_barras": cod, "categoria_id": 1, "cantidad": 10,
        "fecha_vencimiento": (date.today() + timedelta(days=dias)).isoformat(),
    }
    datos.update(extra)
    return datos


# ---------- autenticación ----------
def test_login_incorrecto_mensaje_generico(client):
    r = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "mala"})
    assert r.status_code == 401
    r2 = client.post("/api/auth/login", json={"email": "nadie@test.com", "password": "mala"})
    assert r.json() == r2.json()


def test_rutas_protegidas_sin_token(client):
    assert client.get("/api/productos").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_registro_publico_crea_operador_y_rechaza_duplicado(client):
    nuevo = {"nombre": "Ana", "email": "ana@test.com", "password": "Otra-clave-123"}
    r = client.post("/api/auth/register", json=nuevo)
    assert r.status_code == 201 and r.json()["rol"] == "operador"
    assert "password" not in r.text and "hash" not in r.text
    assert client.post("/api/auth/register", json=nuevo).status_code == 409


def test_registro_valida_password_corta(client):
    r = client.post("/api/auth/register", json={"nombre": "Ana", "email": "ana@test.com", "password": "corta"})
    assert r.status_code == 422


def test_usuario_inactivo_no_puede_entrar(client, admin, db):
    uid = client.get("/api/usuarios", headers=admin).json()
    op = next(u for u in uid if u["email"] == "op@test.com")
    assert client.put(f"/api/usuarios/{op['id']}", json={"activo": False}, headers=admin).status_code == 200
    r = client.post("/api/auth/login", json={"email": "op@test.com", "password": PASSWORD})
    assert r.status_code == 401


def test_cambiar_password(client, operador):
    r = client.post("/api/auth/cambiar-password", json={"actual": "incorrecta", "nueva": "Nueva-clave-1"}, headers=operador)
    assert r.status_code == 400
    r = client.post("/api/auth/cambiar-password", json={"actual": PASSWORD, "nueva": "Nueva-clave-1"}, headers=operador)
    assert r.status_code == 204
    assert client.post("/api/auth/login", json={"email": "op@test.com", "password": "Nueva-clave-1"}).status_code == 200


# ---------- permisos ----------
def test_operador_no_accede_a_usuarios_ni_categorias_admin(client, operador):
    assert client.get("/api/usuarios", headers=operador).status_code == 403
    assert client.post("/api/categorias", json={"nombre": "Nueva"}, headers=operador).status_code == 403


def test_admin_no_puede_degradarse_a_si_mismo(client, admin):
    yo = client.get("/api/auth/me", headers=admin).json()
    assert yo["rol"] == "administrador"
    assert client.put(f"/api/usuarios/{yo['id']}", json={"rol": "operador"}, headers=admin).status_code == 400
    assert client.put(f"/api/usuarios/{yo['id']}", json={"activo": False}, headers=admin).status_code == 400


# ---------- categorías ----------
def test_categorias_crud_y_eliminar(client, admin, operador):
    r = client.post("/api/categorias", json={"nombre": "Snacks"}, headers=admin)
    assert r.status_code == 201
    cid = r.json()["id"]
    assert client.post("/api/categorias", json={"nombre": "Snacks"}, headers=admin).status_code == 409
    assert client.put(f"/api/categorias/{cid}", json={"nombre": "Snacks 2"}, headers=admin).json()["nombre"] == "Snacks 2"
    client.post("/api/productos", json=producto(categoria_id=cid), headers=operador)
    # con productos asociados NO se puede eliminar
    assert client.delete(f"/api/categorias/{cid}", headers=admin).status_code == 409
    vacia = client.post("/api/categorias", json={"nombre": "Vacia"}, headers=admin).json()["id"]
    assert client.delete(f"/api/categorias/{vacia}", headers=operador).status_code == 403
    assert client.delete(f"/api/categorias/{vacia}", headers=admin).status_code == 204


# ---------- productos ----------
def test_producto_crud_completo(client, operador, admin):
    r = client.post("/api/productos", json=producto("A1", dias=100), headers=operador)
    assert r.status_code == 201
    p = r.json()
    assert p["estado"] == "vigente" and p["dias_restantes"] == 100 and p["categoria"] == "Lácteos"
    pid = p["id"]
    editado = producto("A1", dias=5, nombre="Leche entera")
    r = client.put(f"/api/productos/{pid}", json=editado, headers=operador)
    assert r.json()["estado"] == "proximo" and r.json()["nombre"] == "Leche entera"
    assert client.delete(f"/api/productos/{pid}", headers=operador).status_code == 403
    assert client.delete(f"/api/productos/{pid}", headers=admin).status_code == 204
    assert client.get(f"/api/productos/{pid}", headers=admin).status_code == 404


def test_producto_se_asigna_al_usuario_que_lo_crea(client, operador, db):
    from app.models import Producto

    pid = client.post("/api/productos", json=producto("U1"), headers=operador).json()["id"]
    assert db.get(Producto, pid).usuario_id == client.get("/api/auth/me", headers=operador).json()["id"]


def test_validaciones_de_producto(client, operador):
    sin_fecha = producto()
    del sin_fecha["fecha_vencimiento"]
    for malo in (producto(cantidad=-1), producto(nombre="x"), producto(categoria_id=999), sin_fecha):
        assert client.post("/api/productos", json=malo, headers=operador).status_code == 422


def test_estados_segun_fecha_y_filtros(client, operador):
    for cod, dias in (("V", -3), ("P", 10), ("G", 200)):
        client.post("/api/productos", json=producto(cod, dias), headers=operador)
    for estado, esperado in (("vencido", "V"), ("proximo", "P"), ("vigente", "G")):
        items = client.get(f"/api/productos?estado={estado}", headers=operador).json()["items"]
        assert [i["codigo_barras"] for i in items] == [esperado], estado
        assert items[0]["estado"] == estado
    assert client.get("/api/productos?estado=inventado", headers=operador).status_code == 422


def test_busqueda_orden_y_paginacion(client, operador):
    for i in range(1, 6):
        client.post("/api/productos", json=producto(f"S{i}", dias=i * 10, nombre=f"Item {i}"), headers=operador)
    r = client.get("/api/productos?page_size=2&page=2&ordenar_por=fecha_vencimiento&orden=asc", headers=operador).json()
    assert r["total"] == 5 and [i["codigo_barras"] for i in r["items"]] == ["S3", "S4"]
    ult = client.get("/api/productos?ordenar_por=fecha_vencimiento&orden=desc&page_size=100", headers=operador).json()["items"]
    assert ult[0]["codigo_barras"] == "S5"
    assert client.get("/api/productos?q=Item 3", headers=operador).json()["total"] == 1
    assert client.get("/api/productos?q=S4", headers=operador).json()["total"] == 1  # por código de barras
    assert client.get("/api/productos?ordenar_por=password_hash", headers=operador).status_code == 422


def test_stock(client, operador):
    pid = client.post("/api/productos", json=producto("ST"), headers=operador).json()["id"]
    assert client.patch(f"/api/productos/{pid}/stock", json={"delta": -4}, headers=operador).json()["cantidad"] == 6
    assert client.patch(f"/api/productos/{pid}/stock", json={"delta": -7}, headers=operador).status_code == 422
    assert client.patch(f"/api/productos/{pid}/stock", json={"cantidad": 50}, headers=operador).json()["cantidad"] == 50
    assert client.patch(f"/api/productos/{pid}/stock", json={}, headers=operador).status_code == 422


def test_umbral_por_usuario_cambia_estados(client, operador, admin):
    client.post("/api/productos", json=producto("U", dias=20), headers=operador)
    assert client.get("/api/productos", headers=operador).json()["items"][0]["estado"] == "proximo"  # por defecto 30
    assert client.put("/api/config-alertas", json={"dias_alerta": 10}, headers=operador).json() == {"dias_alerta": 10}
    assert client.put("/api/config-alertas", json={"dias_alerta": 12}, headers=operador).json() == {"dias_alerta": 12}
    assert client.get("/api/productos", headers=operador).json()["items"][0]["estado"] == "vigente"
    # la configuración es por usuario: el administrador conserva el umbral por defecto
    assert client.get("/api/productos", headers=admin).json()["items"][0]["estado"] == "proximo"
    assert client.put("/api/config-alertas", json={"dias_alerta": 0}, headers=operador).status_code == 422


def png(texto=None):
    img = np.full((300, 900, 3), 255, np.uint8)
    if texto:
        cv2.putText(img, texto, (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 3)
    return cv2.imencode(".png", img)[1].tobytes()


def test_foto_de_producto(client, operador):
    pid = client.post("/api/productos", json=producto("F"), headers=operador).json()["id"]
    assert client.get(f"/api/productos/{pid}/foto", headers=operador).status_code == 404
    r = client.post(f"/api/productos/{pid}/foto", files={"archivo": ("a.png", png(), "image/png")}, headers=operador)
    assert r.status_code == 204
    assert client.get(f"/api/productos/{pid}/foto", headers=operador).status_code == 200
    r = client.post(f"/api/productos/{pid}/foto", files={"archivo": ("a.png", b"no soy imagen", "image/png")}, headers=operador)
    assert r.status_code == 400


# ---------- OCR (con el motor simulado: aquí no se prueba Tesseract) ----------
def subir(client, headers):
    return client.post("/api/scan", files={"archivo": ("e.png", png(), "image/png")}, headers=headers)


def test_flujo_scan_confirmar_actualiza_producto(client, operador, monkeypatch):
    monkeypatch.setattr(vision, "leer_texto", lambda variantes: "LOTE: AB123\nVENC: 25/12/2030")
    pid = client.post("/api/productos", json=producto("O", dias=5), headers=operador).json()["id"]

    r = subir(client, operador)
    assert r.status_code == 200
    scan = r.json()
    assert scan["requiere_confirmacion"] and scan["sugerida"]["fecha"] == "2030-12-25"
    assert scan["lotes"] == ["AB123"]
    # el escaneo por sí solo NO modifica el producto ni el historial
    assert client.get(f"/api/productos/{pid}", headers=operador).json()["fecha_vencimiento"] != "2030-12-25"
    assert client.get("/api/historial", headers=operador).json()["total"] == 0

    cuerpo = {"scan_id": scan["scan_id"], "fecha": "2030-12-25", "producto_id": pid}
    r = client.post("/api/scan/confirmar", json=cuerpo, headers=operador)
    assert r.status_code == 200 and r.json()["resultado"] == "confirmada"
    assert client.get(f"/api/productos/{pid}", headers=operador).json()["fecha_vencimiento"] == "2030-12-25"
    assert client.post("/api/scan/confirmar", json=cuerpo, headers=operador).status_code == 404  # ya resuelto
    det = client.get(f"/api/productos/{pid}/detecciones", headers=operador).json()
    assert len(det) == 1 and det[0]["resultado"] == "confirmada"
    assert client.get(f"/api/historial/{r.json()['id']}/imagen", headers=operador).status_code == 200


def test_scan_fecha_corregida_y_descartada(client, operador, admin, monkeypatch):
    monkeypatch.setattr(vision, "leer_texto", lambda v: "VENC: 25/12/2030")
    sid = subir(client, operador).json()["scan_id"]
    # otro usuario no puede resolver el escaneo ajeno
    assert client.post("/api/scan/confirmar", json={"scan_id": sid, "fecha": "2031-01-01"}, headers=admin).status_code == 404
    r = client.post("/api/scan/confirmar", json={"scan_id": sid, "fecha": "2031-01-01"}, headers=operador)
    assert r.json()["resultado"] == "corregida"
    sid2 = subir(client, operador).json()["scan_id"]
    assert client.delete(f"/api/scan/{sid2}", headers=operador).status_code == 204
    assert client.post("/api/scan/confirmar", json={"scan_id": sid2, "fecha": "2031-01-01"}, headers=operador).status_code == 404
    assert client.post("/api/scan/confirmar", json={"scan_id": "../../x", "fecha": "2031-01-01"}, headers=operador).status_code == 422
    assert client.get("/api/historial?resultado=corregida", headers=operador).json()["total"] == 1
    assert client.get("/api/historial?resultado=confirmada", headers=operador).json()["total"] == 0


def test_scan_ilegible_no_inventa_fechas(client, operador, monkeypatch):
    monkeypatch.setattr(vision, "leer_texto", lambda v: "")
    r = subir(client, operador).json()
    assert r["candidatas"] == [] and r["sugerida"] is None and r["advertencias"]
    assert client.get("/api/historial", headers=operador).json()["total"] == 0


def test_scan_rechaza_archivo_invalido_y_sin_tesseract(client, operador, monkeypatch):
    r = client.post("/api/scan", files={"archivo": ("x.png", b"MZ" + b"0" * 300, "image/png")}, headers=operador)
    assert r.status_code == 400
    monkeypatch.setattr(vision, "_localizar_tesseract", lambda: None)
    assert subir(client, operador).status_code == 503
    assert client.get("/api/historial", headers=operador).json()["total"] == 0  # nada se registra


# ---------- dashboard, alertas, reportes ----------
def test_dashboard_alertas_y_estadisticas(client, operador):
    for cod, dias in (("V", -3), ("P", 10), ("P2", 15), ("G", 200)):
        client.post("/api/productos", json=producto(cod, dias), headers=operador)
    d = client.get("/api/dashboard", headers=operador).json()
    assert d["por_estado"] == {"vencido": 1, "proximo": 2, "vigente": 1, "sin_fecha": 0}
    assert d["total_productos"] == 4 and d["unidades_en_stock"] == 40
    assert [p["codigo_barras"] for p in d["proximos"]] == ["P", "P2"]
    a = client.get("/api/alertas?estado=vencido", headers=operador).json()
    assert a["total"] == 1 and a["items"][0]["dias_restantes"] == -3 and a["resumen"]["proximo"] == 2
    e = client.get("/api/estadisticas?meses=3", headers=operador).json()
    assert len(e["evolucion"]) == 3 and e["evolucion"][-1]["productos"] == 4
    assert {c["categoria"]: c["productos"] for c in e["por_categoria"]}["Lácteos"] == 4
    assert sum(m["productos"] for m in e["vencimientos_proximos"]) >= 2


# ---------- frontend estático ----------
def test_frontend_se_sirve_y_api_no_se_pisa(client):
    r = client.get("/")
    assert r.status_code == 200 and "InvenVision" in r.text
    assert client.get("/js/main.js").status_code == 200
    assert client.get("/api/ruta-que-no-existe").status_code == 404
