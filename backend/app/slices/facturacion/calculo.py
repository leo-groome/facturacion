"""Helpers de cálculo fiscal CFDI 4.0 con precisión Decimal.

Reglas SAT:
- Cálculos internos a 6 decimales.
- Totales presentados a 2 decimales.
- Tolerancia de ±0.01 al comparar importes que vienen del cliente.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Tuple

from fastapi import HTTPException, status

from .schema import Concepto, Impuesto

SIX = Decimal("0.000001")
TWO = Decimal("0.01")
TOLERANCIA = Decimal("0.01")

IVA_TASA = Decimal("0.16")
ISR_RESICO_TASA = Decimal("0.0125")
RESICO_REGIMEN = "626"


# ---------------------------------------------------------------------------
# Matriz UsoCFDI x RegimenFiscal del receptor
# Fuente: SAT - Anexo 20 Rev. 2022 (vigente 2024-2026)
# ---------------------------------------------------------------------------

_INGRESOS_ACTIVIDAD_PM = {
    "G01", "G02", "G03",
    "I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08",
    "CP01", "S01",
}
_INGRESOS_ACTIVIDAD_PF = {
    "G01", "G02", "G03",
    "I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08",
    "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10",
    "CP01", "S01",
}

USO_CFDI_POR_REGIMEN: dict[str, set[str]] = {
    "601": _INGRESOS_ACTIVIDAD_PM,
    "603": _INGRESOS_ACTIVIDAD_PM,
    "605": {"CN01", "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "CP01", "S01"},
    "606": _INGRESOS_ACTIVIDAD_PF,
    "607": {"D04", "CP01", "S01"},
    "608": _INGRESOS_ACTIVIDAD_PF,
    "610": _INGRESOS_ACTIVIDAD_PM,
    "611": {"CP01", "S01"},
    "612": _INGRESOS_ACTIVIDAD_PF,
    "614": {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "CP01", "S01"},
    "615": {"D04", "CP01", "S01"},
    "616": {"CP01", "S01"},
    "620": _INGRESOS_ACTIVIDAD_PM,
    "621": _INGRESOS_ACTIVIDAD_PF,
    "622": _INGRESOS_ACTIVIDAD_PF,
    "623": _INGRESOS_ACTIVIDAD_PM,
    "624": _INGRESOS_ACTIVIDAD_PM,
    "625": _INGRESOS_ACTIVIDAD_PF,
    "626": _INGRESOS_ACTIVIDAD_PF,
}


def validar_uso_cfdi(regimen_receptor: str, uso_cfdi: str) -> None:
    """Verifica UsoCFDI compatible con régimen fiscal del receptor (Anexo 20 SAT)."""
    permitidos = USO_CFDI_POR_REGIMEN.get(regimen_receptor)
    if permitidos is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Regimen fiscal del receptor '{regimen_receptor}' no reconocido en catalogo SAT.",
        )
    if uso_cfdi not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"UsoCFDI '{uso_cfdi}' no es compatible con el regimen fiscal del receptor "
                f"'{regimen_receptor}' segun el Anexo 20 SAT."
            ),
        )


def usos_cfdi_permitidos(regimen_receptor: str) -> List[str]:
    """Retorna los UsoCFDI aceptados para un régimen receptor (ordenados)."""
    return sorted(USO_CFDI_POR_REGIMEN.get(regimen_receptor, set()))


def aplicar_retencion_resico(
    regimen_emisor: str,
    rfc_emisor: str,
    rfc_receptor: str,
    subtotal: Decimal,
) -> Decimal:
    """ISR 1.25% sobre subtotal si emisor RESICO PF y receptor PM; si no, 0."""
    if regimen_emisor == RESICO_REGIMEN and len(rfc_emisor) == 13 and len(rfc_receptor) == 12:
        return q2(subtotal * ISR_RESICO_TASA)
    return Decimal("0.00")


def q6(x: Decimal) -> Decimal:
    return x.quantize(SIX, rounding=ROUND_HALF_UP)


def q2(x: Decimal) -> Decimal:
    return x.quantize(TWO, rounding=ROUND_HALF_UP)


def _es_persona_moral(rfc: str) -> bool:
    """RFC de 12 caracteres = Persona Moral. 13 caracteres = Persona Física."""
    return len(rfc.strip()) == 12


def _es_persona_fisica(rfc: str) -> bool:
    return len(rfc.strip()) == 13


def _buscar_impuesto(impuestos: Iterable[Impuesto], tipo: str, es_retencion: bool) -> Impuesto | None:
    return next(
        (i for i in impuestos if i.tipo == tipo and i.es_retencion == es_retencion),
        None,
    )


def validar_y_totalizar(
    conceptos: list[Concepto],
    emisor_regimen: str,
    receptor_rfc: str,
    emisor_rfc: str = "",
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """Valida impuestos por concepto y retorna (subtotal, traslados, retenciones, total) a 2 decimales.

    Regla SAT (art. 113-J LISR): la retención ISR 1.25% solo aplica cuando el
    emisor RESICO es Persona Física y el receptor es Persona Moral. Si el
    emisor es PM (también en 626) no existe retención automática.
    """
    exige_isr_resico = (
        emisor_regimen == RESICO_REGIMEN
        and _es_persona_fisica(emisor_rfc)
        and _es_persona_moral(receptor_rfc)
    )

    subtotal = Decimal("0")
    traslados = Decimal("0")
    retenciones = Decimal("0")

    for c in conceptos:
        base_concepto = q6(c.importe - c.descuento)
        subtotal += base_concepto

        if c.objeto_imp != "02":
            # 01/03/04 no participan en el desglose estándar de impuestos aquí.
            continue

        # Validar que cada impuesto tenga base congruente
        for imp in c.impuestos:
            if abs(imp.base - base_concepto) > TOLERANCIA:
                raise ValueError(
                    f"Base del impuesto {imp.tipo} en '{c.descripcion}' "
                    f"({imp.base}) no coincide con importe-descuento ({base_concepto})."
                )
            esperado = q6(imp.base * imp.tasa)
            if abs(imp.importe - esperado) > TOLERANCIA:
                raise ValueError(
                    f"Importe del impuesto {imp.tipo} en '{c.descripcion}' "
                    f"({imp.importe}) difiere del esperado ({esperado})."
                )

        # IVA trasladado obligatorio al 16% (si hay cualquier IVA)
        iva = _buscar_impuesto(c.impuestos, "IVA", es_retencion=False)
        if iva is None:
            raise ValueError(
                f"El concepto '{c.descripcion}' con ObjetoImp=02 requiere IVA trasladado."
            )
        traslados += iva.importe

        # IEPS opcional
        ieps = _buscar_impuesto(c.impuestos, "IEPS", es_retencion=False)
        if ieps is not None:
            traslados += ieps.importe

        # Retención ISR 1.25% obligatoria si emisor RESICO + receptor PM
        if exige_isr_resico:
            isr = _buscar_impuesto(c.impuestos, "ISR", es_retencion=True)
            isr_esperado = q6(base_concepto * ISR_RESICO_TASA)
            if isr is None:
                raise ValueError(
                    f"Emisor RESICO (626) y receptor Persona Moral: falta retención ISR "
                    f"1.25% en '{c.descripcion}' (esperado {isr_esperado})."
                )
            if abs(isr.importe - isr_esperado) > TOLERANCIA:
                raise ValueError(
                    f"Retención ISR RESICO en '{c.descripcion}' ({isr.importe}) "
                    f"difiere del esperado ({isr_esperado})."
                )
            retenciones += isr.importe

        # Retención IVA opcional
        iva_ret = _buscar_impuesto(c.impuestos, "IVA_RET", es_retencion=True)
        if iva_ret is not None:
            retenciones += iva_ret.importe

    total = subtotal + traslados - retenciones
    return q2(subtotal), q2(traslados), q2(retenciones), q2(total)
