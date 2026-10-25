from app.services.date_parser import extraer_fechas, sugerir


def fechas(texto):
    return [(c.fecha, c.tipo) for c in extraer_fechas(texto)]


def test_vencimiento_con_etiqueta():
    assert fechas("VENC: 25/12/2026") == [("2026-12-25", "vencimiento")]


def test_distingue_fabricacion_y_vencimiento_en_la_misma_linea():
    r = fechas("FAB: 01/03/2026 VENC: 01/03/2027")
    assert r == [("2026-03-01", "fabricacion"), ("2027-03-01", "vencimiento")]


def test_etiquetas_en_lineas_distintas():
    r = fechas("ELAB 10-01-2026\nEXP 10-01-2027")
    assert r == [("2026-01-10", "fabricacion"), ("2027-01-10", "vencimiento")]


def test_sin_etiqueta_es_desconocido_y_no_se_sugiere():
    c = extraer_fechas("25/12/2026")
    assert c[0].tipo == "desconocido"
    assert sugerir(c) is None


def test_mes_y_anio_usa_ultimo_dia():
    assert fechas("CAD 02/2028") == [("2028-02-29", "vencimiento")]
    assert fechas("BEST BEFORE 11/26") == [("2026-11-30", "vencimiento")]


def test_mes_en_texto():
    assert fechas("VTO 15 ENE 2027") == [("2027-01-15", "vencimiento")]
    assert fechas("EXP JAN 2027") == [("2027-01-31", "vencimiento")]


def test_iso():
    assert fechas("EXP 2027-03-09") == [("2027-03-09", "vencimiento")]


def test_ambigua_se_marca_y_no_se_sugiere():
    c = extraer_fechas("VENC 03/04/2027")
    assert c[0].ambigua is True
    assert sugerir(c) is None


def test_no_ambigua_si_dia_mayor_a_12():
    c = extraer_fechas("VENC 25/04/2027")
    assert c[0].ambigua is False
    assert sugerir(c).fecha == "2027-04-25"


def test_fecha_invalida_se_descarta():
    assert extraer_fechas("VENC 31/02/2027") == []
    assert extraer_fechas("VENC 40/13/2027") == []


def test_texto_sin_fechas_o_vacio():
    assert extraer_fechas("") == []
    assert extraer_fechas(None) == []
    assert extraer_fechas("LOTE A123 PESO 500G") == []


def test_no_sugiere_si_hay_dos_vencimientos():
    c = extraer_fechas("EXP 25/04/2027 EXP 26/04/2027")
    assert sugerir(c) is None


def test_lotes_solo_con_etiqueta():
    from app.services.date_parser import extraer_lotes

    assert extraer_lotes("LOTE: AB123 VENC 01/01/2027") == ["AB123"]
    assert extraer_lotes("Lot 7788-X\nL#C9912") == ["7788-X", "C9912"]
    assert extraer_lotes("PESO 500G SIN ETIQUETA A1B2C3") == []
