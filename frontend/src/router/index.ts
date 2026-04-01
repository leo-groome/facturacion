import { createRouter, createWebHistory } from 'vue-router'
import OnboardingView from '../views/OnboardingView.vue'
import EmisionView from '../views/EmisionView.vue'
import ExploradorView from '../views/ExploradorView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/onboarding'
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

export default router
