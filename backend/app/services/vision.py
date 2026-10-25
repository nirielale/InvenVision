"""Validación, preprocesamiento y OCR de imágenes de etiquetas."""
import os
import shutil
from pathlib import Path

import cv2
import numpy as np

from app.config import settings

from app.services.date_parser import extraer_fechas, extraer_lotes, sugerir

MAX_BYTES = 8 * 1024 * 1024
MAX_LADO = 4000
MIN_LADO = 100
FIRMAS = {b"\xff\xd8\xff": "jpeg", b"\x89PNG\r\n\x1a\n": "png"}


class ImagenInvalida(ValueError):
    pass


class OcrNoDisponible(RuntimeError):
    pass


def validar_imagen(datos: bytes) -> np.ndarray:
    """Valida tamaño, formato real (por firma, no por extensión) y dimensiones."""
    if not datos:
        raise ImagenInvalida("El archivo está vacío")
    if len(datos) > MAX_BYTES:
        raise ImagenInvalida(f"La imagen supera el máximo de {MAX_BYTES // (1024 * 1024)} MB")
    es_webp = datos[:4] == b"RIFF" and datos[8:12] == b"WEBP"
    if not es_webp and not any(datos.startswith(f) for f in FIRMAS):
        raise ImagenInvalida("Formato no permitido. Use JPEG, PNG o WEBP")
    img = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ImagenInvalida("No se pudo leer la imagen; puede estar dañada")
    alto, ancho = img.shape[:2]
    if min(alto, ancho) < MIN_LADO:
        raise ImagenInvalida(f"La imagen es demasiado pequeña (mínimo {MIN_LADO}px por lado)")
    if max(alto, ancho) > MAX_LADO:
        raise ImagenInvalida(f"La imagen es demasiado grande (máximo {MAX_LADO}px por lado)")
    return img


def extension(datos: bytes) -> str:
    """Extensión según la firma real del archivo (ya validado)."""
    if datos[:3] == bytes([0xFF, 0xD8, 0xFF]):
        return "jpg"
    return "png" if datos[1:4] == b"PNG" else "webp"


def preprocesar(img: np.ndarray) -> list[np.ndarray]:
    """Devuelve variantes en escala de grises para mejorar la lectura del OCR."""
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    alto, ancho = gris.shape
    if max(alto, ancho) < 1600:  # ampliar texto pequeño
        f = 1600 / max(alto, ancho)
        gris = cv2.resize(gris, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    suave = cv2.fastNlMeansDenoising(gris, None, 10)
    contraste = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(suave)
    umbral = cv2.adaptiveThreshold(
        contraste, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    return [contraste, umbral]


def _localizar_tesseract() -> str | None:
    candidatos = [
        settings.tesseract_cmd or os.environ.get("TESSERACT_CMD"),
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    return next((c for c in candidatos if c and Path(c).exists()), None)


def ocr_disponible() -> bool:
    return _localizar_tesseract() is not None


def leer_texto(variantes: list[np.ndarray]) -> str:
    ruta = _localizar_tesseract()
    if ruta is None:
        raise OcrNoDisponible(
            "Tesseract no está instalado. Instálelo o defina TESSERACT_CMD en el .env"
        )
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = ruta
    textos = []
    for v in variantes:
        textos.append(pytesseract.image_to_string(v, lang="spa+eng", config="--psm 6"))
    return "\n".join(textos)


def escanear(datos: bytes) -> dict:
    """Pipeline completo. No guarda nada: devuelve candidatas para confirmar."""
    img = validar_imagen(datos)
    texto = leer_texto(preprocesar(img))
    candidatas = _unicas(extraer_fechas(texto))
    sugerida = sugerir(candidatas)
    advertencias = []
    if not texto.strip():
        advertencias.append("No se reconoció texto. La imagen puede estar borrosa u oscura.")
    elif not candidatas:
        advertencias.append("Se leyó texto pero no se encontró ninguna fecha.")
    if candidatas and sugerida is None:
        advertencias.append("No hay una fecha de vencimiento clara; seleccione o corrija manualmente.")
    return {
        "texto": texto.strip(),
        "candidatas": [c.to_dict() for c in candidatas],
        "sugerida": sugerida.to_dict() if sugerida else None,
        "lotes": extraer_lotes(texto),
        "requiere_confirmacion": True,
        "advertencias": advertencias,
    }


def _unicas(candidatas):
    vistas, salida = set(), []
    for c in candidatas:  # las variantes repiten texto; se conserva la primera
        clave = (c.fecha, c.tipo)
        if clave not in vistas:
            vistas.add(clave)
            salida.append(c)
    return salida
