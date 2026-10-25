"""Lógica central de estados de vencimiento. Única fuente de verdad del backend."""
from datetime import date

ESTADO_VENCIDO = "vencido"
ESTADO_PROXIMO = "proximo"
ESTADO_VIGENTE = "vigente"
ESTADO_SIN_FECHA = "sin_fecha"


def dias_restantes(vencimiento: date | None, hoy: date | None = None) -> int | None:
    if vencimiento is None:
        return None
    return (vencimiento - (hoy or date.today())).days


def clasificar(
    vencimiento: date | None, umbral_dias: int, hoy: date | None = None
) -> tuple[str, int | None]:
    """Devuelve (estado, días restantes).

    El producto se considera vigente/próximo hasta el final del día de su
    fecha de vencimiento: con 0 días restantes aún no está vencido.
    """
    if umbral_dias < 0:
        raise ValueError("El umbral de días no puede ser negativo")
    dias = dias_restantes(vencimiento, hoy)
    if dias is None:
        return ESTADO_SIN_FECHA, None
    if dias < 0:
        return ESTADO_VENCIDO, dias
    if dias <= umbral_dias:
        return ESTADO_PROXIMO, dias
    return ESTADO_VIGENTE, dias
