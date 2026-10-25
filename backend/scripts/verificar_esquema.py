"""Compara los modelos del backend con el esquema REAL de MySQL. Solo lectura.

Uso (desde la carpeta backend):
    python -m scripts.verificar_esquema

Termina con código 0 si todas las tablas y columnas de los modelos existen en la base.
"""
import sys

from sqlalchemy import inspect

from app import models  # noqa: F401
from app.database import Base, engine


def main() -> int:
    insp = inspect(engine)
    reales = set(insp.get_table_names())
    problemas = 0
    for tabla in Base.metadata.sorted_tables:
        if tabla.name not in reales:
            print(f"FALTA tabla {tabla.name}")
            problemas += 1
            continue
        cols = {c["name"]: c for c in insp.get_columns(tabla.name)}
        for col in tabla.columns:
            real = cols.get(col.name)
            if real is None:
                print(f"FALTA columna {tabla.name}.{col.name}")
                problemas += 1
            elif real["nullable"] != col.nullable and not col.primary_key:
                print(f"AVISO nulabilidad {tabla.name}.{col.name}: modelo={col.nullable} real={real['nullable']}")
                problemas += 1
        extra = set(cols) - {c.name for c in tabla.columns}
        if extra:
            print(f"AVISO columnas reales sin usar en {tabla.name}: {sorted(extra)}")
    print("Esquema compatible." if not problemas else f"{problemas} diferencia(s).")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
