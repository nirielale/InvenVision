from datetime import date

import pytest

from app.services.expiry import clasificar, dias_restantes

HOY = date(2026, 6, 15)


def test_vencido():
    assert clasificar(date(2026, 6, 14), 30, HOY) == ("vencido", -1)


def test_vence_hoy_aun_no_esta_vencido():
    assert clasificar(date(2026, 6, 15), 30, HOY) == ("proximo", 0)


def test_limite_del_umbral_es_proximo():
    assert clasificar(date(2026, 7, 15), 30, HOY) == ("proximo", 30)


def test_justo_sobre_el_umbral_es_vigente():
    assert clasificar(date(2026, 7, 16), 30, HOY) == ("vigente", 31)


def test_sin_fecha():
    assert clasificar(None, 30, HOY) == ("sin_fecha", None)
    assert dias_restantes(None) is None


def test_umbral_negativo_rechazado():
    with pytest.raises(ValueError):
        clasificar(HOY, -1, HOY)
