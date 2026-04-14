import axios from 'axios'

// Configuración base de Axios apuntando al backend FastAPI
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor global para inyectar JWT, garantizando el aislamiento Multitenant
api.interceptors.request.use(
  (config) => {
    // Extrae el JWT de localStorage para la sesión actual
    const token = localStorage.getItem('token')

    if (token) {
      if (!config.headers) {
        config.headers = {} as any
      }
      config.headers['Authorization'] = `Bearer ${token}`
    }

    if (!config.headers) {
      config.headers = {} as any
    }
    // Fallback provisional o de localStorage para el multi-tenant (evita el 422 de Header required)
    config.headers['x-organization-id'] = localStorage.getItem('organization_id') || 'tenant_default_123'

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Si el token expira o es inválido, podríamos limpiar y redirigir
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized API call. JWT valid?")
      // localStorage.removeItem('token')
      // window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
