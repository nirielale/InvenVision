import cv2
import numpy as np
import pytest

from app.services import vision


def png(ancho=400, alto=200, texto=None):
    img = np.full((alto, ancho, 3), 255, np.uint8)
    if texto:
        cv2.putText(img, texto, (10, alto // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def test_acepta_png_valido():
    assert vision.validar_imagen(png()).shape == (200, 400, 3)


def test_rechaza_vacio():
    with pytest.raises(vision.ImagenInvalida):
        vision.validar_imagen(b"")


def test_rechaza_formato_falso_aunque_tenga_extension_de_imagen():
    with pytest.raises(vision.ImagenInvalida, match="Formato"):
        vision.validar_imagen(b"MZ" + b"\x00" * 500)


def test_rechaza_demasiado_grande():
    with pytest.raises(vision.ImagenInvalida, match="máximo"):
        vision.validar_imagen(b"\xff\xd8\xff" + b"0" * (vision.MAX_BYTES + 1))


def test_rechaza_firma_valida_pero_contenido_corrupto():
    with pytest.raises(vision.ImagenInvalida, match="leer"):
        vision.validar_imagen(b"\x89PNG\r\n\x1a\n" + b"basura" * 50)


def test_rechaza_imagen_diminuta():
    with pytest.raises(vision.ImagenInvalida, match="pequeña"):
        vision.validar_imagen(png(50, 50))


def test_preprocesar_devuelve_variantes_2d_escaladas():
    variantes = vision.preprocesar(vision.validar_imagen(png()))
    assert len(variantes) == 2
    assert all(v.ndim == 2 and max(v.shape) >= 1600 for v in variantes)


def test_sin_tesseract_el_error_es_explicito(monkeypatch):
    monkeypatch.setattr(vision, "_localizar_tesseract", lambda: None)
    with pytest.raises(vision.OcrNoDisponible):
        vision.escanear(png())


@pytest.mark.skipif(not vision.ocr_disponible(), reason="Tesseract no instalado")
def test_ocr_real_sobre_imagen_sintetica():
    r = vision.escanear(png(900, 200, "EXP 25/12/2027"))
    assert r["requiere_confirmacion"] is True
