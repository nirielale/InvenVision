"""Inserta productos de DEMOSTRACIÓN claramente identificados (SKU que empieza con "DEMO-").

Uso (desde la carpeta backend):
    python -m scripts.datos_demo --confirmar            # agrega los datos
    python -m scripts.datos_demo --confirmar --quitar   # elimina SOLO los SKU "DEMO-"

Nunca borra ni modifica datos reales; sin --confirmar no hace nada.
Requiere que exista al menos una categoría activa.
"""
import sys
from datetime import date, timedelta

from app.database import SessionLocal
from app.models import Categoria, Producto

DEMO = [
    ("DEMO-001", "Leche entera 1L (demo)", -5, 24), ("DEMO-002", "Yogurt fresa 500g (demo)", 4, 40),
    ("DEMO-003", "Queso fresco 250g (demo)", 12, 15), ("DEMO-004", "Jugo de naranja 1L (demo)", 25, 60),
    ("DEMO-005", "Galletas de avena (demo)", 90, 120), ("DEMO-006", "Atún en lata (demo)", 400, 200),
    ("DEMO-007", "Mantequilla 200g (demo)", -20, 8), ("DEMO-008", "Cereal integral (demo)", 55, 35),
]


def main() -> int:
    if "--confirmar" not in sys.argv:
        print("Sin --confirmar no se realiza ningún cambio. Lea el encabezado del script.")
        return 1
    with SessionLocal() as db:
        if "--quitar" in sys.argv:
            n = db.query(Producto).filter(Producto.sku.like("DEMO-%")).delete(synchronize_session=False)
            db.commit()
            print(f"Eliminados {n} productos demo.")
            return 0
        cat = db.query(Categoria).filter(Categoria.activa.is_(True)).order_by(Categoria.id).first()
        if cat is None:
            print("No hay categorías activas; cree una primero.")
            return 1
        creados = 0
        for sku, nombre, dias, cantidad in DEMO:
            if db.query(Producto).filter(Producto.sku == sku).first():
                continue
            db.add(Producto(nombre=nombre, sku=sku, categoria_id=cat.id, cantidad=cantidad, precio_costo=3.5,
                            proveedor="Proveedor demo", fecha_vencimiento=date.today() + timedelta(days=dias)))
            creados += 1
        db.commit()
        print(f"Creados {creados} productos demo en la categoría «{cat.nombre}».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
