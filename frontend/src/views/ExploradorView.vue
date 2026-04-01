<script setup lang="ts">
import DataGrid from '@/components/explorador/DataGrid.vue'
</script>

<template>
  <div class="explorador-view min-h-screen bg-slate-50 p-6 sm:p-12 font-sans text-slate-900">
    <div class="max-w-6xl mx-auto">
      <h1 class="text-4xl font-black mb-2 tracking-tight">Registro de Comprobantes</h1>
      <p class="text-slate-500 mb-8 font-medium text-lg">Administrador documental y herramienta de trazabilidad segura Multitenant.</p>
      
      <DataGrid />
    </div>
  </div>
</template>
