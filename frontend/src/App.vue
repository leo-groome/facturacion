<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navLinks = [
  { name: 'Onboarding', path: '/onboarding', label: 'Configuración Fiscal' },
  { name: 'Emisión', path: '/emision', label: 'Nueva Factura' },
  { name: 'Explorador', path: '/explorador', label: 'Mis Facturas' },
  { name: 'API Keys', path: '/apikeys', label: 'Desarrolladores' }
]

const tenantRfc = computed(() => authStore.user?.org ?? '')
const avatarLetters = computed(() => tenantRfc.value.slice(0, 2).toUpperCase() || '?')

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden font-sans">
    <!-- Sidebar -->
    <aside v-if="!route.meta.public" class="w-72 bg-slate-900 text-white flex flex-col border-r border-slate-800">
      <div class="p-8">
        <h1 class="text-3xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
          VANTA
        </h1>
        <p class="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Billing System</p>
      </div>

      <nav class="flex-1 px-4 space-y-1 mt-4">
        <RouterLink
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="flex items-center px-4 py-3 text-sm font-semibold rounded-xl transition-all duration-200 group"
          :class="route.path === link.path ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40' : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
        >
          {{ link.label }}
        </RouterLink>
      </nav>

      <div class="p-4 border-t border-slate-800 space-y-2">
        <div class="flex items-center gap-3 px-4 py-3 bg-slate-800/50 rounded-2xl border border-slate-700/50">
          <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center font-bold text-xs shrink-0">
            {{ avatarLetters }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-bold text-white truncate">{{ tenantRfc || 'Sin sesión' }}</p>
            <p class="text-[10px] text-slate-500 truncate">Tenant activo</p>
          </div>
        </div>
        <button
          @click="handleLogout"
          class="w-full text-xs font-semibold text-slate-500 hover:text-red-400 transition-colors py-1"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>

    <!-- Content Area -->
    <main class="flex-1 overflow-y-auto bg-white/50 backdrop-blur-sm relative" :class="{ 'p-0': route.meta.public }">
      <div v-if="!route.meta.public" class="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,#fff,rgba(255,255,255,0.6))] -z-10"></div>
      <div :class="route.meta.public ? '' : 'max-w-7xl mx-auto p-8 lg:p-12'">
        <RouterView v-slot="{ Component }">
          <transition 
            enter-active-class="transition duration-300 ease-out"
            enter-from-class="opacity-0 translate-y-4"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-200 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 -translate-y-4"
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  font-family: 'Inter', sans-serif;
}

body {
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

.bg-grid-slate-100 {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32' fill='none' stroke='rgb(241 245 249 / 1)'%3E%3Cpath d='M0 .5H31.5V32'/%3E%3C/svg%3E");
}
</style>
