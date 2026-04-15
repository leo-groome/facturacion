import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

interface TenantUser {
  id: string
  org: string
}

function parseJwtPayload(token: string): TenantUser | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]!))
    if (typeof payload.id === 'string' && typeof payload.org === 'string') {
      return { id: payload.id, org: payload.org }
    }
    return null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const rawToken = localStorage.getItem('token')
  const validToken = (rawToken && rawToken !== 'null' && rawToken !== 'undefined') ? rawToken : null

  const token = ref<string | null>(validToken)
  const user = ref<TenantUser | null>(validToken ? parseJwtPayload(validToken) : null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(rfc: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/auth/login', { rfc, password })
      const accessToken: string = response.data.access_token
      token.value = accessToken
      user.value = parseJwtPayload(accessToken)
      localStorage.setItem('token', accessToken)
      return true
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail ?? 'Error al iniciar sesión'
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
      return await login(rfc, password)
    } catch (err: any) {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (Array.isArray(detail)) {
          error.value = detail.map((d: any) => d.msg).join(', ')
        } else {
          error.value = detail
        }
      } else {
        error.value = 'Error de red o CORS al intentar conectarse al servidor.'
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
