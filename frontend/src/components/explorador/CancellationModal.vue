<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'

const props = defineProps<{
  show: boolean
  facturaId: string
  folioFiscal: string
}>()

const emit = defineEmits(['close', 'cancelled'])

const isSubmitting = ref(false)
const formData = ref({
  motivo: '02',
  folio_sustituto: ''
})

const submitCancellation = async () => {
  if (formData.value.motivo === '01' && !formData.value.folio_sustituto) {
    alert("Para la clave 01, es obligatorio indicar el Folio que la sustituye.")
    return
  }
  
  try {
    isSubmitting.value = true
    await api.post(`/facturacion/${props.facturaId}/cancelar`, {
      folio_fiscal: props.folioFiscal,
      motivo: formData.value.motivo,
      folio_sustituto: formData.value.motivo === '01' ? formData.value.folio_sustituto : null
    })
    
    alert("La factura ha entrado a proceso de cancelación con el integrador.")
    emit('cancelled')
    emit('close')
  } catch(error: any) {
    alert("Fallo la petición: " + (error.response?.data?.detail || error.message))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 bg-slate-900 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
    <div class="p-8 border w-[550px] shadow-2xl rounded-xl bg-white">
      <div class="text-left">
        <h3 class="text-2xl font-bold text-slate-900 mb-2 mt-0">Cancelar CFDI</h3>
        <p class="text-slate-500 text-sm mb-6">Especifica el motivo de la cancelación para la factura con UUID: <br/><strong class="font-mono text-xs">{{folioFiscal}}</strong></p>
        
        <form @submit.prevent="submitCancellation" class="space-y-5">
          <div>
            <label class="block text-sm font-semibold mb-2">Clave de Cancelación SAT</label>
            <select v-model="formData.motivo" class="w-full border border-slate-300 rounded-lg p-3 bg-slate-50 focus:ring-2 focus:ring-red-500 outline-none">
              <option value="01">01 - Comprobante emitido con errores con relación</option>
              <option value="02">02 - Comprobante emitido con errores sin relación</option>
              <option value="03">03 - No se llevó a cabo la operación</option>
              <option value="04">04 - Operación nominativa relacionada en una factura global</option>
            </select>
          </div>
          
          <div v-if="formData.motivo === '01'" class="animate-fade-in">
            <label class="block text-sm font-semibold mb-2">Folio Sustituto (UUID)</label>
            <input v-model="formData.folio_sustituto" type="text" placeholder="UUID del comprobante de reemplazo" class="w-full border border-slate-300 rounded-lg p-3 bg-slate-50 focus:ring-2 focus:ring-red-500 outline-none font-mono text-sm" />
          </div>
          
          <div class="flex items-center gap-3 mt-8 pt-4 border-t border-slate-100">
            <button @click="$emit('close')" type="button" class="px-5 py-2.5 bg-slate-100 text-slate-700 font-semibold rounded-lg hover:bg-slate-200 w-full transition-colors">Abortar</button>
            <button :disabled="isSubmitting" type="submit" class="px-5 py-2.5 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 w-full disabled:bg-red-400 transition-colors">
              {{ isSubmitting ? 'Procesando API...' : 'Confirmar Cancelación' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
