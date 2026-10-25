"""Mide el OCR de fechas con imágenes REALES etiquetadas por usted.

Uso (desde la carpeta backend, con Tesseract instalado):
    python ..\\ml\\evaluar_ocr.py ruta\\a\\carpeta

La carpeta debe contener imágenes (.jpg/.png) y, junto a cada una, un .txt con la fecha de
vencimiento correcta en formato AAAA-MM-DD (o la palabra NINGUNA si la etiqueta no tiene fecha legible).
Reporta cuántas veces la fecha SUGERIDA coincide, cuántas veces la fecha correcta aparece entre
las candidatas, y cuántas veces el sistema se abstuvo (sin sugerencia). No hay cifras de precisión
publicadas: se obtienen únicamente de este experimento.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services import vision  # noqa: E402


def main(carpeta: Path) -> int:
    if not vision.ocr_disponible():
        print("Tesseract no está disponible.")
        return 1
    imagenes = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    total = acierto_sugerida = en_candidatas = abstenciones = sugerencia_erronea = 0
    for img in imagenes:
        etiqueta = img.with_suffix(".txt")
        if not etiqueta.exists():
            continue
        real = etiqueta.read_text(encoding="utf-8").strip()
        try:
            r = vision.escanear(img.read_bytes())
        except vision.ImagenInvalida as e:
            print(f"{img.name}: imagen inválida ({e})")
            continue
        total += 1
        sug = r["sugerida"]["fecha"] if r["sugerida"] else None
        if sug is None:
            abstenciones += 1
        elif sug == real:
            acierto_sugerida += 1
        else:
            sugerencia_erronea += 1
        if real in {c["fecha"] for c in r["candidatas"]}:
            en_candidatas += 1
        print(f"{img.name}: real={real} sugerida={sug}")
    if not total:
        print("No se encontraron imágenes con su archivo .txt.")
        return 1
    print(f"\nImágenes evaluadas: {total}")
    print(f"Sugerida correcta:          {acierto_sugerida}/{total}")
    print(f"Sugerida incorrecta:        {sugerencia_erronea}/{total}")
    print(f"Sin sugerencia (abstención): {abstenciones}/{total}")
    print(f"Fecha correcta entre candidatas: {en_candidatas}/{total}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(main(Path(sys.argv[1])))
