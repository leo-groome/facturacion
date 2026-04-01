<script setup lang="ts">
import KeyManager from '@/components/apikeys/KeyManager.vue'
</script>

<template>
  <div class="apikeys-view min-h-screen bg-slate-50 p-6 sm:p-12 font-sans tracking-wide">
    <div class="max-w-5xl mx-auto">
      <h1 class="text-4xl font-black mb-8 text-slate-900 drop-shadow-sm">Desarrolladores & Access Tokens</h1>
      <KeyManager />
    </div>
  </div>
</template>
