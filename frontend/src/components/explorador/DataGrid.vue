<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import CancellationModal from './CancellationModal.vue'

const facturas = ref<any[]>([])
const isLoading = ref(true)

const isCancelModalOpen = ref(false)
const selectedFactura = ref<any>(null)

const fetchFacturas = async () => {
  isLoading.value = true
  try {
    const { data } = await api.get('/facturacion/')
    facturas.value = data.data
  } catch (error) {
    console.error("Error al obtener capa de datos", error)
  } finally {
    isLoading.value = false
  }
}

const openCancelFlow = (factura: any) => {
  selectedFactura.value = factura
  isCancelModalOpen.value = true
}

// Implementación de descargas a prueba de IDOR/Exposición con Blobs (promesa XHR)
const triggerDownload = async (facturaId: string, format: string) => {
  try {
    const response = await api.get(`/facturacion/${facturaId}/download/${format}`, {
      responseType: 'blob'
    })
    
    // Create virtual anchor using blob
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `CFDI_${facturaId}.${format}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
  } catch (error) {
    alert(`Error al descargar formato ${format}`)
  }
}

onMounted(() => {
  fetchFacturas()
})
</script>

<template>
  <div class="data-grid bg-white border border-slate-200 shadow-sm rounded-xl overflow-hidden mt-6">
    <div class="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
      <h3 class="font-bold text-slate-800 text-lg">Explorador Documental </h3>
      <button @click="fetchFacturas" class="px-4 py-2 border border-slate-200 shadow-sm bg-white hover:bg-slate-50 rounded-lg text-sm font-semibold transition-colors">Recargar Datos</button>
    </div>
    
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm whitespace-nowrap">
        <thead class="bg-white text-slate-500 uppercase text-xs font-bold border-b border-slate-200">
          <tr>
            <th class="px-6 py-4">Status</th>
            <th class="px-6 py-4">Folio Fiscal (UUID)</th>
            <th class="px-6 py-4">Receptor</th>
            <th class="px-6 py-4">Emisión</th>
            <th class="px-6 py-4 text-right">Total</th>
            <th class="px-6 py-4 text-center">Acciones y Descargas</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="isLoading">
            <td colspan="6" class="px-6 py-12 text-center text-slate-500">
              <svg class="animate-spin h-6 w-6 text-indigo-500 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Sincronizando con base de datos real...
            </td>
          </tr>
          <tr v-else-if="!facturas.length">
            <td colspan="6" class="px-6 py-12 text-center text-slate-500">No hay facturas timbradas o emitidas por esta organización.</td>
          </tr>
          <tr v-for="cfdi in facturas" :key="cfdi.id" class="hover:bg-slate-50 transition-colors">
            <td class="px-6 py-4">
              <span :class="cfdi.estado === 'Timbrado' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'" class="px-2 py-1 rounded font-bold text-xs">
                {{ cfdi.estado }}
              </span>
            </td>
            <td class="px-6 py-4 font-mono text-xs text-slate-600 font-medium">{{ cfdi.folio_fiscal }}</td>
            <td class="px-6 py-4">
              <div class="font-bold text-slate-800">{{ cfdi.receptor_razon_social }}</div>
              <div class="text-xs text-slate-500">{{ cfdi.receptor_rfc }}</div>
            </td>
            <td class="px-6 py-4 text-slate-600">{{ new Date(cfdi.fecha_emision).toLocaleDateString() }}</td>
            <td class="px-6 py-4 text-right font-bold text-slate-800">${{ cfdi.total.toFixed(2) }}</td>
            <td class="px-6 py-4">
              <div class="flex justify-center gap-2">
                <button @click="triggerDownload(cfdi.id, 'pdf')" class="px-3 py-1 bg-white border border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-300 rounded font-medium text-xs transition-colors">PDF</button>
                <button @click="triggerDownload(cfdi.id, 'xml')" class="px-3 py-1 bg-white border border-slate-200 text-slate-600 hover:text-orange-600 hover:border-orange-300 rounded font-medium text-xs transition-colors">XML</button>
                <button @click="triggerDownload(cfdi.id, 'zip')" class="px-3 py-1 bg-white border border-slate-200 text-slate-600 hover:text-emerald-600 hover:border-emerald-300 rounded font-medium text-xs transition-colors">ZIP</button>
                <button v-if="cfdi.estado === 'Timbrado'" @click="openCancelFlow(cfdi)" class="px-3 py-1 bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 rounded font-bold text-xs transition-colors ml-2">Cancelar</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <CancellationModal 
      :show="isCancelModalOpen" 
      :facturaId="selectedFactura?.id || ''" 
      :folioFiscal="selectedFactura?.folio_fiscal || ''"
      @close="isCancelModalOpen = false" 
      @cancelled="fetchFacturas"
    />
  </div>
</template>
