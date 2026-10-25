"""Extracción de fechas candidatas desde texto OCR.

Nunca decide por el usuario: devuelve candidatas con su texto de origen, el tipo
inferido por contexto (vencimiento / fabricación / desconocido) y banderas de
ambigüedad. La confirmación final es siempre del usuario.

Formatos reconocidos: AAAA-MM-DD, DD/MM/AAAA, DD-MM-AA, DD.MM.AAAA,
DD MES AAAA (p. ej. 15 ENE 2026), MES AAAA (ENE 2026, JAN/26) y MM/AAAA, MM/AA.
Los separadores admitidos son "/", "-", "." y espacio. Se asume el orden
día-mes-año; si día y mes son ≤ 12 y distintos, se marca como ambigua.
Las fechas con solo mes y año se resuelven al último día de ese mes.
"""
import calendar
import re
from dataclasses import asdict, dataclass
from datetime import date

TIPO_VENCIMIENTO = "vencimiento"
TIPO_FABRICACION = "fabricacion"
TIPO_DESCONOCIDO = "desconocido"

_MESES = {
    "ENERO": 1, "ENE": 1, "JAN": 1, "FEBRERO": 2, "FEB": 2, "MARZO": 3, "MAR": 3,
    "ABRIL": 4, "ABR": 4, "APR": 4, "MAYO": 5, "MAY": 5, "JUNIO": 6, "JUN": 6,
    "JULIO": 7, "JUL": 7, "AGOSTO": 8, "AGO": 8, "AUG": 8, "SETIEMBRE": 9,
    "SEPTIEMBRE": 9, "SEP": 9, "SET": 9, "OCTUBRE": 10, "OCT": 10,
    "NOVIEMBRE": 11, "NOV": 11, "DICIEMBRE": 12, "DIC": 12, "DEC": 12,
}
_MES_RE = "|".join(sorted(_MESES, key=len, reverse=True))

_PATRONES = [
    ("AAAA-MM-DD", re.compile(r"(?<!\d)(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})(?!\d)")),
    ("DD/MM/AAAA", re.compile(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})(?!\d)")),
    ("DD MES AAAA", re.compile(rf"(?<!\d)(\d{{1,2}})\s*[/\-. ]?\s*({_MES_RE})\s*[/\-. ]?\s*(\d{{4}}|\d{{2}})(?![\dA-Z])")),
    ("MES AAAA", re.compile(rf"(?<![\dA-Z])({_MES_RE})\s*[/\-. ]?\s*(\d{{4}}|\d{{2}})(?![\dA-Z])")),
    ("MM/AAAA", re.compile(r"(?<!\d)(\d{1,2})[/\-.](\d{4}|\d{2})(?!\d)")),
]

_CLAVE_VENC = re.compile(
    r"\b(?:EXP\w*|VENC\w*|VTO\.?|CAD\w*|BEST\s*BEFORE|BBE?|USE\s*BY|CONSUMIR|C\.?\s*PREF\w*|CONS\.?\s*PREF\w*)"
)
_CLAVE_FAB = re.compile(
    r"\b(?:FAB\w*|ELAB\w*|PROD\w*|MFG|MANUF\w*|PKD|PACK\w*|ENV\w*|LOTE\s*FECHA)"
)


@dataclass
class Candidata:
    texto: str
    fecha: str  # ISO AAAA-MM-DD
    formato: str
    tipo: str
    ambigua: bool
    confianza: float
    nota: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _anio(valor: str) -> int:
    n = int(valor)
    return 2000 + n if len(valor) == 2 else n


def _construir(formato: str, g: tuple) -> tuple[date, bool, str] | None:
    """Devuelve (fecha, ambigua, nota) o None si la fecha no es válida."""
    try:
        if formato == "AAAA-MM-DD":
            return date(int(g[0]), int(g[1]), int(g[2])), False, ""
        if formato == "DD/MM/AAAA":
            d, m, a = int(g[0]), int(g[1]), _anio(g[2])
            ambigua = d <= 12 and m <= 12 and d != m
            return date(a, m, d), ambigua, "Día y mes ≤ 12: se asumió DD/MM." if ambigua else ""
        if formato == "DD MES AAAA":
            return date(_anio(g[2]), _MESES[g[1]], int(g[0])), False, ""
        if formato in ("MES AAAA", "MM/AAAA"):
            m = _MESES[g[0]] if formato == "MES AAAA" else int(g[0])
            a = _anio(g[1])
            return date(a, m, calendar.monthrange(a, m)[1]), False, "Solo mes y año: se usó el último día del mes."
    except (ValueError, KeyError):
        return None
    return None


def _tipo_por_contexto(previo: str) -> str:
    previo = previo[-30:]
    ultima_venc = max((m.end() for m in _CLAVE_VENC.finditer(previo)), default=-1)
    ultima_fab = max((m.end() for m in _CLAVE_FAB.finditer(previo)), default=-1)
    if ultima_venc < 0 and ultima_fab < 0:
        return TIPO_DESCONOCIDO
    return TIPO_VENCIMIENTO if ultima_venc > ultima_fab else TIPO_FABRICACION


def extraer_fechas(texto: str) -> list[Candidata]:
    texto = re.sub(r"[ \t]+", " ", (texto or "").upper())
    ocupado: list[tuple[int, int]] = []
    halladas = []  # (inicio, fin, formato, texto, fecha, ambigua, nota)

    for formato, patron in _PATRONES:
        for m in patron.finditer(texto):
            if any(m.start() < fin and m.end() > ini for ini, fin in ocupado):
                continue
            construida = _construir(formato, m.groups())
            if construida is None:
                continue
            ocupado.append(m.span())
            halladas.append((m.start(), m.end(), formato, m.group(0).strip(), *construida))

    halladas.sort(key=lambda h: h[0])
    candidatas = []
    fin_anterior = 0
    for inicio, fin, formato, original, fecha, ambigua, nota in halladas:
        # El contexto es el texto de la misma línea desde la fecha anterior
        desde = max(texto.rfind("\n", 0, inicio) + 1, fin_anterior)
        tipo = _tipo_por_contexto(texto[desde:inicio])
        base = {TIPO_VENCIMIENTO: 0.9, TIPO_DESCONOCIDO: 0.4, TIPO_FABRICACION: 0.2}[tipo]
        candidatas.append(Candidata(
            texto=original, fecha=fecha.isoformat(), formato=formato, tipo=tipo,
            ambigua=ambigua, confianza=round(base - (0.2 if ambigua else 0), 2), nota=nota,
        ))
        fin_anterior = fin
    return candidatas


def sugerir(candidatas: list[Candidata]) -> Candidata | None:
    """Sugiere una candidata solo si no hay duda razonable; si no, None."""
    venc = [c for c in candidatas if c.tipo == TIPO_VENCIMIENTO and not c.ambigua]
    return venc[0] if len(venc) == 1 else None
