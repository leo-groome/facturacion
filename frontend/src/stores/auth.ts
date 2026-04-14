import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const initialToken = localStorage.getItem('token')
  const token = ref<string | null>(
    (initialToken && initialToken !== 'null' && initialToken !== 'undefined') ? initialToken : null
  )
  const user = ref<any>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(rfc: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/auth/login', { rfc, password })
      token.value = response.data.access_token
      localStorage.setItem('token', token.value!)
      // Optional: Store organization_id if returned
      if (response.data.organization_id) {
        localStorage.setItem('organization_id', response.data.organization_id)
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al iniciar sesión'
      return false
    } finally {
      loading.value = false
    }
  }

  async function signUp(nombre_empresa: string, rfc: string, password: string) {
    loading.value = true
    error.value = null
    try {
      await api.post('/auth/signup', { nombre_empresa, rfc, password })
      // Auto login after sign up if backend supports it, or just return success
      return await login(rfc, password)
    } catch (err: any) {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          error.value = detail.map((d: any) => d.msg).join(", ");
        } else {
          error.value = detail;
        }
      } else {
        error.value = 'Error de red o CORS al intentar conectarse al servidor.';
      }
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('organization_id')
  }

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    login,
    signUp,
    logout
  }
})
