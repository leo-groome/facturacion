<script setup lang="ts">
import { ref, watch } from 'vue'
import { useFacturacionStore } from '@/stores/facturacion'
import api from '@/services/api'

const store = useFacturacionStore()
const searchKeyword = ref('')
const searchResults = ref<any[]>([])
const isSearching = ref(false)

const draftTotal = ref<number | null>(null)

// Predictivo con debounce
let debounceTimer: ReturnType<typeof setTimeout>
watch(searchKeyword, (newVal) => {
  clearTimeout(debounceTimer)
  if (newVal.length < 3) {
    searchResults.value = []
    return
  }
  
  debounceTimer = setTimeout(async () => {
    isSearching.value = true
    try {
      const response = await api.get(`/catalogos/prodserv?keyword=${newVal}`)
      searchResults.value = response.data.resultados
    } catch (e) {
      console.error(e)
    } finally {
      isSearching.value = false
    }
  }, 500)
})

const selectCatalog = (val: any) => {
  store.addConcepto({
    clave_prod_serv: val.Value,
    cantidad: 1,
    valor_unitario: 1000.00,
    importe: 1000.00,
    descuento: 0,
    impuestos: [
      { tipo: 'IVA', tasa: 0.160000, importe: 160.00 }
    ]
  })
  searchKeyword.value = ''
  searchResults.value = []
}

const previewFactura = async () => {
  try {
    const draftPayload = {
      receptor_rfc: store.receptorRfc || 'XAXX010101000',
      receptor_razon_social: 'Regimen Simulado',
      receptor_regimen: '616',
      receptor_domicilio_fiscal: '00000',
      conceptos: store.conceptos
    }
    const { data } = await api.post('/facturacion/preview', draftPayload)
    draftTotal.value = data.total
    alert(`Borrador generado con éxito! \nValidado Localmente sin timbrar.\nTotal M.N: $${data.total}`)
  } catch (error: any) {
    alert("Error al simular: " + (error.response?.data?.detail || error.message))
  }
}
</script>

<template>
  <div class="smart-form bg-white shadow-xl rounded-xl p-8 border border-slate-100">
    <h2 class="text-2xl font-black mb-6 text-slate-800 tracking-tight">Generador de CFDI 4.0</h2>
    
    <div class="mb-6 grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-2">RFC Receptor</label>
        <input v-model="store.receptorRfc" type="text" class="p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition-all bg-slate-50" placeholder="XAXX010101000" />
      </div>
    </div>
    
    <div class="mb-8">
      <h3 class="text-lg font-bold mb-4 text-slate-700">Conceptos (Partidas)</h3>
      <div class="relative mb-4">
        <label class="block text-sm font-semibold text-slate-700 mb-2">Buscador Predictivo SAT</label>
        <input v-model="searchKeyword" type="text" class="p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 transition-all shadow-sm" placeholder="Buscar por Producto o Servicio (Ej. Computadoras...)" />
        <ul v-if="searchResults.length" class="absolute z-20 w-full bg-white border border-slate-200 mt-2 shadow-2xl rounded-lg max-h-56 overflow-y-auto hidden-scrollbar">
          <li v-for="res in searchResults" :key="res.Value" @click="selectCatalog(res)" class="p-3 hover:bg-emerald-50 cursor-pointer border-b border-slate-100 last:border-0 transition-colors">
            <span class="font-mono text-emerald-700 font-bold bg-emerald-100 px-2 py-1 rounded text-xs mr-2">{{res.Value}}</span> 
            <span class="text-slate-700">{{res.Name}}</span>
          </li>
        </ul>
        <div v-if="isSearching" class="text-xs text-slate-500 mt-2 flex items-center gap-2">
           <svg class="animate-spin h-4 w-4 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
           Buscando en catálogos del SAT...
        </div>
      </div>
      
      <div v-if="store.conceptos.length" class="space-y-3">
        <div v-for="(concepto, idx) in store.conceptos" :key="idx" class="p-4 bg-slate-50 rounded-lg border border-slate-200 flex justify-between items-center group">
          <div>
            <div class="font-semibold text-slate-800">Concepto {{concepto.clave_prod_serv}}</div>
            <div class="text-sm text-slate-500">{{concepto.cantidad}} x ${{concepto.valor_unitario}}</div>
          </div>
          <button @click="store.removeConcepto(idx)" class="text-red-500 hover:text-red-700 font-bold opacity-0 group-hover:opacity-100 transition-opacity">Eliminar</button>
        </div>
      </div>
    </div>
    
    <div class="bg-gradient-to-br from-slate-50 to-slate-100 p-6 rounded-xl mb-8 border border-slate-200">
      <div class="text-right space-y-3">
        <p class="text-sm font-semibold text-slate-500 flex justify-end gap-6"><span>Subtotal:</span> <span class="text-slate-800 w-24">${{ store.subtotal.toFixed(2) }}</span></p>
        <p class="text-sm font-semibold text-slate-500 flex justify-end gap-6"><span>IVA/IEPS Trasladados:</span> <span class="text-slate-800 w-24">${{ store.totalImpuestosTrasladados.toFixed(2) }}</span></p>
        <div class="w-full h-px bg-slate-200 my-2"></div>
        <p class="text-2xl font-black text-slate-900 flex justify-end gap-6 items-center"><span class="text-sm font-semibold text-slate-500 pb-1">Total M.N:</span> <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-teal-500">${{ store.total.toFixed(2) }}</span></p>
      </div>
    </div>
    
    <button @click="previewFactura" class="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-md hover:shadow-lg flex justify-center items-center gap-2 disabled:opacity-50" :disabled="!store.conceptos.length">
      Generar Vista Previa (Simulador)
    </button>
  </div>
</template>
