import { createRouter, createWebHistory } from 'vue-router'
import OnboardingView from '../views/OnboardingView.vue'
import EmisionView from '../views/EmisionView.vue'
import ExploradorView from '../views/ExploradorView.vue'
import AuthView from '../views/AuthView.vue'

const isAuthenticated = () => {
  const token = localStorage.getItem('token')
  return !!(token && token !== 'null' && token !== 'undefined')
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      meta: { public: true }
    },
    {
      path: '/',
      redirect: () => {
        return isAuthenticated() ? { name: 'onboarding' } : { name: 'login' }
      }
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: OnboardingView
    },
    {
      path: '/emision',
      name: 'emision',
      component: EmisionView
    },
    {
      path: '/explorador',
      name: 'explorador',
      component: ExploradorView
    },
    {
      path: '/apikeys',
      name: 'apikeys',
      component: () => import('../views/ApiKeysView.vue')
    }
  ],
})

/**
 * Global Navigation Guard:
 * 1. Protege todas las rutas que no tienen el flag 'public'.
 * 2. Redirige al login si no hay token.
 * 3. Si el usuario ya está autenticado, previene el acceso al login enviándolo a onboarding.
 */
router.beforeEach((to, from, next) => {
  const loggedIn = isAuthenticated()

  if (!to.meta.public && !loggedIn) {
    // Intento de acceder a ruta privada sin estar autenticado
    next({ name: 'login' })
  } else if (to.name === 'login' && loggedIn) {
    // Usuario ya autenticado intentando volver al login
    next({ name: 'onboarding' })
  } else {
    // Permitir navegación
    next()
  }
})

export default router
