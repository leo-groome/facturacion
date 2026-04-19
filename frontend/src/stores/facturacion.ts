import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Impuesto {
  tipo: string
  tasa: number
  importe: number
}

export interface Concepto {
  clave_prod_serv: string
  clave_unidad: string
  descripcion: string
  cantidad: number
  valor_unitario: number
  importe: number
  descuento: number
  impuestos: Impuesto[]
}

export const useFacturacionStore = defineStore('facturacion', () => {
  const receptorRfc = ref('')
  const conceptos = ref<Concepto[]>([])
  
  const subtotal = computed(() => {
    return conceptos.value.reduce((acc, c) => acc + (c.importe - c.descuento), 0)
  })

  const totalImpuestosTrasladados = computed(() => {
    let sum = 0
    conceptos.value.forEach(c => {
      c.impuestos.filter(i => i.tipo === 'IVA' || i.tipo === 'IEPS').forEach(i => sum += i.importe)
    })
    return sum
  })

  const totalImpuestosRetenidos = computed(() => {
    let sum = 0
    conceptos.value.forEach(c => {
      c.impuestos.filter(i => i.tipo === 'ISR' || i.tipo === 'IVA_RET').forEach(i => sum += i.importe)
    })
    return sum
  })

  const total = computed(() => {
    return subtotal.value + totalImpuestosTrasladados.value - totalImpuestosRetenidos.value
  })

  function addConcepto(concepto: Concepto) {
    conceptos.value.push(concepto)
  }

  function removeConcepto(index: number) {
    conceptos.value.splice(index, 1)
  }

  return {
    receptorRfc,
    conceptos,
    subtotal,
    totalImpuestosTrasladados,
    totalImpuestosRetenidos,
    total,
    addConcepto,
    removeConcepto
  }
})
