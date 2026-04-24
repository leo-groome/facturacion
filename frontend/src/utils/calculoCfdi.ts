import Decimal from 'decimal.js'

Decimal.set({ precision: 28, rounding: Decimal.ROUND_HALF_UP })

export const IVA_TASA = '0.16'
export const ISR_RESICO_TASA = '0.0125'
export const RESICO_REGIMEN = '626'

export type ObjetoImp = '01' | '02' | '03' | '04'
export type TipoImpuesto = 'IVA' | 'IEPS' | 'ISR' | 'IVA_RET'

export interface Impuesto {
  tipo: TipoImpuesto
  tasa: number
  base: number
  importe: number
  es_retencion: boolean
}

export interface Concepto {
  clave_prod_serv: string
  clave_unidad: string
  descripcion: string
  cantidad: number
  valor_unitario: number
  importe: number
  descuento: number
  objeto_imp: ObjetoImp
  impuestos: Impuesto[]
}

export interface ContextoFiscal {
  emisorRegimen: string
  receptorRfc: string
}

export function esPersonaMoral(rfc: string): boolean {
  return rfc.trim().length === 12
}

function q6(x: Decimal): number {
  return x.toDecimalPlaces(6, Decimal.ROUND_HALF_UP).toNumber()
}

export function q2(x: number | Decimal): number {
  const d = x instanceof Decimal ? x : new Decimal(x)
  return d.toDecimalPlaces(2, Decimal.ROUND_HALF_UP).toNumber()
}

/**
 * Recalcula importe + impuestos de un concepto a partir de cantidad, valor_unitario,
 * descuento, objeto_imp y el contexto fiscal (régimen del emisor + receptor).
 */
export function recalcularConcepto(c: Concepto, ctx: ContextoFiscal): Concepto {
  const cantidad = new Decimal(c.cantidad || 0)
  const precio = new Decimal(c.valor_unitario || 0)
  const descuento = new Decimal(c.descuento || 0)

  const importeD = cantidad.mul(precio)
  const baseD = Decimal.max(importeD.minus(descuento), new Decimal(0))
  const base = q6(baseD)

  const impuestos: Impuesto[] = []

  if (c.objeto_imp === '02' && baseD.gt(0)) {
    impuestos.push({
      tipo: 'IVA',
      tasa: Number(IVA_TASA),
      base,
      importe: q6(baseD.mul(IVA_TASA)),
      es_retencion: false,
    })

    if (ctx.emisorRegimen === RESICO_REGIMEN && esPersonaMoral(ctx.receptorRfc)) {
      impuestos.push({
        tipo: 'ISR',
        tasa: Number(ISR_RESICO_TASA),
        base,
        importe: q6(baseD.mul(ISR_RESICO_TASA)),
        es_retencion: true,
      })
    }
  }

  return {
    ...c,
    importe: q6(importeD),
    impuestos,
  }
}

export function totalConcepto(c: Concepto): number {
  const base = new Decimal(c.importe).minus(c.descuento || 0)
  const traslados = c.impuestos
    .filter((i) => !i.es_retencion)
    .reduce((a, i) => a.plus(i.importe), new Decimal(0))
  const retenciones = c.impuestos
    .filter((i) => i.es_retencion)
    .reduce((a, i) => a.plus(i.importe), new Decimal(0))
  return q2(base.plus(traslados).minus(retenciones))
}
