<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()

const variantClasses: Record<string, string> = {
  success: 'bg-emerald-600 border-emerald-500',
  error: 'bg-rose-600 border-rose-500',
  info: 'bg-slate-800 border-slate-700',
}
</script>

<template>
  <div class="fixed top-6 right-6 z-[100] flex flex-col gap-2 w-80 pointer-events-none">
    <transition-group
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-x-4"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0 translate-x-4"
    >
      <div
        v-for="t in toasts"
        :key="t.id"
        :class="['pointer-events-auto text-white text-sm font-medium px-4 py-3 rounded-xl border shadow-lg flex items-start gap-3', variantClasses[t.variant]]"
      >
        <span class="flex-1 leading-snug">{{ t.message }}</span>
        <button
          class="text-white/70 hover:text-white transition-colors text-lg leading-none"
          @click="dismiss(t.id)"
          aria-label="Cerrar"
        >
          &times;
        </button>
      </div>
    </transition-group>
  </div>
</template>
