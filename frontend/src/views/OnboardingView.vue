<script setup lang="ts">
import CsdUploader from '@/components/onboarding/CsdUploader.vue'
</script>

<template>
  <div class="onboarding-page max-w-2xl mx-auto p-4 py-12">
    <h1 class="text-3xl font-black text-slate-900 mb-2">Configuración Fiscal</h1>
    <p class="text-slate-600 mb-8 font-medium">Onboarding del Emisor y Carga Protegida de Certificados</p>
    
    <CsdUploader />
  </div>
</template>
