import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import Decimal from 'decimal.js'
import {
  q2,
  ISR_RESICO_TASA,
  RESICO_REGIMEN,
  esPersonaMoral,
  type Concepto,
  type Impuesto,
} from '@/utils/calculoCfdi'
import api from '@/services/api'

export type { Concepto, Impuesto }

export type MetodoPago = 'PUE' | 'PPD'

export const useFacturacionStore = defineStore('facturacion', () => {
  const receptorRfc = ref('')
  const conceptos = ref<Concepto[]>([])
  const emisorRegimen = ref<string>('')
  const emisorRfc = ref<string>('')

  // Condiciones de pago. Regla SAT: PPD obliga formaPago='99'.
  const metodoPago = ref<MetodoPago>('PUE')
  const formaPago = ref<string>('01')
  watch(metodoPago, (v) => {
    if (v === 'PPD') formaPago.value = '99'
    else if (formaPago.value === '99') formaPago.value = '01'
  })

  const formasPagoPermitidas = computed<string[]>(() =>
    metodoPago.value === 'PPD'
      ? ['99']
      : ['01', '02', '03', '04', '05', '06', '28'],
  )

  const subtotal = computed(() =>
    q2(
      conceptos.value.reduce(
        (acc, c) => acc.plus(new Decimal(c.importe).minus(c.descuento || 0)),
        new Decimal(0),
      ),
    ),
  )

  const totalImpuestosTrasladados = computed(() =>
    q2(
      conceptos.value.reduce((acc, c) => {
        const suma = c.impuestos
          .filter((i) => !i.es_retencion)
          .reduce((a, i) => a.plus(i.importe), new Decimal(0))
        return acc.plus(suma)
      }, new Decimal(0)),
    ),
  )

  const totalImpuestosRetenidos = computed(() =>
    q2(
      conceptos.value.reduce((acc, c) => {
        const suma = c.impuestos
          .filter((i) => i.es_retencion)
          .reduce((a, i) => a.plus(i.importe), new Decimal(0))
        return acc.plus(suma)
      }, new Decimal(0)),
    ),
  )

  const total = computed(() =>
    q2(
      new Decimal(subtotal.value)
        .plus(totalImpuestosTrasladados.value)
        .minus(totalImpuestosRetenidos.value),
    ),
  )

  const esResico = computed(() => emisorRegimen.value === RESICO_REGIMEN)

  // Proyeccion UI: retencion ISR 1.25% cuando aplica RESICO PF -> PM.
  // Fuente de verdad = backend (el timbre se construye con lo que calcula calculo.py).
  const retencionResicoISR = computed<number>(() => {
    const emisorPF = emisorRfc.value.trim().length === 13
    if (
      esResico.value &&
      emisorPF &&
      esPersonaMoral(receptorRfc.value)
    ) {
      return q2(new Decimal(subtotal.value).mul(ISR_RESICO_TASA))
    }
    return 0
  })

  function addConcepto(concepto: Concepto) {
    conceptos.value.push(concepto)
  }

  function updateConcepto(index: number, concepto: Concepto) {
    conceptos.value[index] = concepto
  }

  function removeConcepto(index: number) {
    conceptos.value.splice(index, 1)
  }

  async function cargarEmisor() {
    try {
      const { data } = await api.get('/emisores/me')
      emisorRegimen.value = data.regimen_fiscal
      emisorRfc.value = data.rfc
    } catch (e) {
      emisorRegimen.value = ''
      emisorRfc.value = ''
      throw e
    }
  }

  return {
    receptorRfc,
    conceptos,
    emisorRegimen,
    emisorRfc,
    esResico,
    metodoPago,
    formaPago,
    formasPagoPermitidas,
    subtotal,
    totalImpuestosTrasladados,
    totalImpuestosRetenidos,
    retencionResicoISR,
    total,
    addConcepto,
    updateConcepto,
    removeConcepto,
    cargarEmisor,
  }
})
