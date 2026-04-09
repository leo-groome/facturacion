<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLogin = ref(true)
const loginForm = reactive({
  rfc: '',
  password: ''
})

const signupForm = reactive({
  nombre_empresa: '',
  rfc: '',
  password: ''
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  authStore.error = null
}

const handleLogin = async () => {
  const success = await authStore.login(loginForm.rfc, loginForm.password)
  if (success) {
    router.push({ name: 'onboarding' })
  }
}

const handleSignup = async () => {
  const success = await authStore.signUp(signupForm.nombre_empresa, signupForm.rfc, signupForm.password)
  if (success) {
    router.push({ name: 'onboarding' })
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#0f172a] relative overflow-hidden px-4">
    <!-- Background Decor -->
    <div class="absolute top-0 -left-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
    <div class="absolute top-0 -right-4 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
    <div class="absolute -bottom-8 left-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>

    <div class="max-w-md w-full z-10">
      <div class="bg-slate-900/80 backdrop-blur-xl p-10 rounded-3xl shadow-2xl border border-slate-700/50">
        <div class="text-center mb-10">
          <h1 class="text-4xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 mb-2">
            VANTA
          </h1>
          <p class="text-slate-400 text-sm font-medium uppercase tracking-widest">Sistema de Facturación</p>
        </div>

        <transition name="fade-slide" mode="out-in">
          <div :key="isLogin ? 'login' : 'signup'">
            <h2 class="text-2xl font-bold text-white mb-2">
              {{ isLogin ? 'Bienvenido de nuevo' : 'Únete a Vanta' }}
            </h2>
            <p class="text-slate-500 text-sm mb-8">
              {{ isLogin ? 'Ingresa tus credenciales para acceder' : 'Completa los datos para empezar a facturar' }}
            </p>

            <form @submit.prevent="isLogin ? handleLogin() : handleSignup()" class="space-y-5">
              <div v-if="!isLogin" class="space-y-1">
                <label class="text-xs font-bold text-slate-400 uppercase ml-1">Nombre de la Empresa</label>
                <input 
                  v-model="signupForm.nombre_empresa"
                  type="text"
                  placeholder="Ej. Mi Empresa S.A."
                  class="w-full bg-slate-800 border border-slate-700 text-white px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-slate-600"
                  required
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-400 uppercase ml-1">RFC</label>
                <input 
                  v-model="(isLogin ? loginForm : signupForm).rfc"
                  type="text"
                  placeholder="XAXX010101000"
                  class="w-full bg-slate-800 border border-slate-700 text-white px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-slate-600 uppercase"
                  required
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-400 uppercase ml-1">Contraseña</label>
                <input 
                  v-model="(isLogin ? loginForm : signupForm).password"
                  type="password"
                  placeholder="••••••••"
                  class="w-full bg-slate-800 border border-slate-700 text-white px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-slate-600"
                  required
                />
              </div>

              <div v-if="authStore.error" class="bg-red-500/10 border border-red-500/20 text-red-500 p-3 rounded-xl text-xs font-medium text-center">
                {{ authStore.error }}
              </div>

              <button 
                type="submit"
                :disabled="authStore.loading"
                class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-500/20 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <span v-if="authStore.loading" class="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"></span>
                {{ isLogin ? 'Iniciar Sesión' : 'Crear Cuenta' }}
              </button>
            </form>

            <div class="mt-8 pt-8 border-t border-slate-800 text-center text-sm text-slate-500">
              {{ isLogin ? '¿No tienes cuenta?' : '¿Ya eres usuario?' }}
              <button @click="toggleMode" class="text-blue-400 font-bold hover:text-blue-300 transition-colors ml-1">
                {{ isLogin ? 'Regístrate' : 'Accede aquí' }}
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@keyframes blob {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}

.animate-blob {
  animation: blob 7s infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}
</style>
