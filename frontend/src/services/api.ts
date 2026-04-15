import axios from 'axios'
import router from '@/router'

// Configuración base de Axios apuntando al backend FastAPI
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor global para inyectar JWT en cada request
// El aislamiento multi-tenant lo deriva el backend exclusivamente del JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
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
    if (error.response && error.response.status === 401) {
      // Evitar loop si el 401 viene del propio endpoint de login
      const isAuthEndpoint = (error.config?.url as string | undefined)?.includes('/auth/')
      if (!isAuthEndpoint) {
        localStorage.removeItem('token')
        router.push({ name: 'login' })
      }
    }
    return Promise.reject(error)
  }
)

export default api
