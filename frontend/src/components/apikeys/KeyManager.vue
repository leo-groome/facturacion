<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const keys = ref<any[]>([])
const isLoading = ref(true)
const isGenerating = ref(false)

const newlyGeneratedKey = ref<string | null>(null)
const newKeyName = ref('')

const fetchKeys = async () => {
  isLoading.value = true
  try {
    const { data } = await api.get('/apikeys/')
    keys.value = data.data
  } catch(e) {
    console.error("Fetch DB error:", e)
  } finally {
    isLoading.value = false
  }
}

const generateKey = async () => {
  if(!newKeyName.value) {
    toast.error('Proporcione un nombre identificador para la llave.')
    return
  }
  isGenerating.value = true
  try {
    const { data } = await api.post('/apikeys/generate', { name: newKeyName.value })
    newlyGeneratedKey.value = data.api_key_plain
    newKeyName.value = ''
    fetchKeys()
  } catch(e: any) {
    let errorDetail = e.message
    if (e.response?.data?.detail) {
      errorDetail = Array.isArray(e.response.data.detail) 
        ? e.response.data.detail.map((d: any) => d.msg).join(', ') 
        : e.response.data.detail
    }
    toast.error('Error al generar llave de transaccion B2B: ' + errorDetail)
  } finally {
    isGenerating.value = false
  }
}

const deleteKey = async (id: string) => {
  if(!confirm("¿Estás seguro de que deseas revocar y eliminar permanentemente esta API Key? Esta acción es irreversible.")) return
  
  try {
    await api.delete(`/apikeys/${id}`)
    fetchKeys()
  } catch(e: any) {
    toast.error('Error al eliminar la llave: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(() => {
  fetchKeys()
})
</script>

<template>
  <div class="api-keys bg-white p-8 rounded-2xl shadow-md border border-slate-100">
    <div class="flex justify-between items-end mb-8 border-b border-slate-100 pb-6">
      <div>
        <h2 class="text-2xl font-extrabold text-slate-800">API Keys de Integración (B2B)</h2>
        <p class="text-slate-500 mt-2 font-medium">Conecta plataformas terceras directamente a tu Motor de Facturación local bajo parámetros de Autenticación M2M (Limitado a 100/req per key/minuto).</p>
      </div>
    </div>
    
    <div v-if="newlyGeneratedKey" class="mb-10 bg-rose-50 border-l-4 border-rose-500 p-6 rounded-lg relative shadow-inner">
      <h3 class="font-bold text-rose-900 text-lg mb-2 flex items-center gap-2">Atención requerida, Token irrecuperable</h3>
      <p class="text-rose-800 mb-4 text-sm font-medium">Copia tu API Key ahora y resguárdala en tu gestor (ej. AWS Secrets, .env local). Por mandato arquitectónico aplicamos HASH bcrypt unidireccional y <strong>jamás</strong> podremos recuperarla si la pierdes.</p>
      <div class="flex gap-4 items-center bg-white p-3 rounded-md border border-rose-200 shadow-sm">
        <code class="text-emerald-700 font-mono text-base font-bold flex-1 overflow-x-auto whitespace-nowrap p-2 bg-slate-50 rounded">{{ newlyGeneratedKey }}</code>
        <button @click="newlyGeneratedKey = null" class="bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold px-6 py-3 rounded-lg transition-colors border border-rose-300">Guardado de forma segura</button>
      </div>
    </div>
    
    <div class="bg-slate-50 p-6 rounded-xl border border-slate-200 mb-10 shadow-sm">
      <h3 class="font-bold text-slate-700 mb-4 text-base">Crear Nuevo Acces Token API</h3>
      <form @submit.prevent="generateKey" class="flex gap-4">
        <input v-model="newKeyName" type="text" placeholder="Ej. Integración WooCommerce, Microservicio Backend Node..." class="flex-1 p-4 rounded-xl border border-slate-300 outline-none focus:ring-4 focus:ring-indigo-100 focus:border-indigo-400 bg-white shadow-sm transition-all" />
        <button :disabled="isGenerating" type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold py-4 px-8 rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-50 min-w-56">
          {{ isGenerating ? 'Generando HASH...' : 'Crear API Key' }}
        </button>
      </form>
    </div>
    
    <div>
      <h3 class="font-bold text-slate-800 mb-6 text-lg">Listado de Llaves Activas</h3>
      <div class="overflow-x-auto rounded-xl border border-slate-200">
        <table class="w-full text-left">
          <thead class="bg-slate-100 text-slate-600 text-xs uppercase font-extrabold tracking-wider">
            <tr>
              <th class="p-4 border-b border-slate-200">Etiqueta / Nombre</th>
              <th class="p-4 border-b border-slate-200">Prefijo Hasheado</th>
              <th class="p-4 text-center border-b border-slate-200">Estado de Uso</th>
              <th class="p-4 text-right border-b border-slate-200">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="isLoading">
              <td colspan="3" class="p-8 text-center text-slate-500 font-medium">Buscando llaves seguras en el motor...</td>
            </tr>
            <tr v-else-if="!keys.length">
              <td colspan="3" class="p-12 text-center text-slate-500">Actualmente no has expedido tokens de API ni llaves programáticas.</td>
            </tr>
            <tr v-for="key in keys" :key="key.id" class="hover:bg-indigo-50/50 transition-colors">
              <td class="p-5 font-bold text-slate-800">{{ key.name }}</td>
              <td class="p-5 font-mono text-slate-500 text-sm">{{ key.prefix }}••••••••</td>
              <td class="p-5 text-center">
                <span class="bg-emerald-100/50 text-emerald-700 text-xs px-3 py-1.5 rounded-full font-bold uppercase tracking-wide border border-emerald-200">Activa (Rate Limit)</span>
              </td>
              <td class="p-5 text-right">
                <button @click="deleteKey(key.id)" class="text-rose-500 hover:text-rose-700 font-bold p-2 hover:bg-rose-50 rounded-lg transition-all" title="Revocar Acces Token">
                  Eliminar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
