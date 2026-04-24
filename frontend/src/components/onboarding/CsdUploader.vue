<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const certFile = ref<File | null>(null)
const keyFile = ref<File | null>(null)
const password = ref('')
const isUploading = ref(false)

const handleUpload = async () => {
  if (!certFile.value || !keyFile.value || !password.value) {
    toast.error('Por favor llene todos los campos (CER, KEY y Contraseña).')
    return
  }
  isUploading.value = true
  const formData = new FormData()
  formData.append('cer_file', certFile.value)
  formData.append('key_file', keyFile.value)
  formData.append('password', password.value)

  try {
    await api.post('/emisores/csd', formData, {
      headers: {
         'Content-Type': 'multipart/form-data'
      }
    })
    toast.success('CSD subido y encriptado exitosamente.')
  } catch (error: any) {
    toast.error('Error al procesar CSD: ' + (error.response?.data?.detail || error.message))
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <div class="csd-uploader p-6 bg-white rounded-xl shadow border border-slate-200">
    <h3 class="font-bold text-xl mb-4 text-slate-800">Carga de Certificados CSD</h3>
    <p class="text-sm text-slate-500 mb-6 font-medium">Sube tus archivos .cer y .key. Serán cifrados con AES usando CSD_ENCRYPTION_KEY.</p>
    <form @submit.prevent="handleUpload" class="space-y-4">
      <div>
        <label class="block text-sm font-semibold mb-2">Archivo .cer</label>
        <input type="file" @change="(e) => certFile = (e.target as HTMLInputElement).files?.[0] || null" accept=".cer" class="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" />
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Archivo .key</label>
        <input type="file" @change="(e) => keyFile = (e.target as HTMLInputElement).files?.[0] || null" accept=".key" class="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" />
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Contraseña Privada</label>
        <input v-model="password" type="password" placeholder="Contraseña del CSD" class="w-full border border-slate-300 rounded-lg p-3 bg-slate-50 focus:ring-2 focus:ring-indigo-500 outline-none" />
      </div>
      <button :disabled="isUploading" type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 mt-4 rounded-xl shadow transition-colors disabled:opacity-50">
        {{ isUploading ? 'Subiendo seguro...' : 'Cargar CSD' }}
      </button>
    </form>
  </div>
</template>
