<script setup lang="ts">
import { ref, watch } from 'vue'
import api from '@/services/api'

interface CatalogoItem {
  Value: string
  Name: string
}

const props = defineProps<{
  endpoint: 'prodserv' | 'unidades'
  modelValue: string
  placeholder?: string
  minChars?: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
  (e: 'select', item: CatalogoItem): void
}>()

const keyword = ref('')
const results = ref<CatalogoItem[]>([])
const isSearching = ref(false)
const showDropdown = ref(false)
const minChars = props.minChars ?? 3

let timer: ReturnType<typeof setTimeout> | null = null

watch(keyword, (val) => {
  if (timer) clearTimeout(timer)
  if (val.length < minChars) {
    results.value = []
    showDropdown.value = false
    return
  }
  timer = setTimeout(async () => {
    isSearching.value = true
    try {
      const { data } = await api.get(`/catalogos/${props.endpoint}?keyword=${encodeURIComponent(val)}`)
      results.value = data.resultados ?? []
      showDropdown.value = results.value.length > 0
    } catch (e) {
      console.error(`Error buscando /catalogos/${props.endpoint}:`, e)
      results.value = []
    } finally {
      isSearching.value = false
    }
  }, 500)
})

function onSelect(item: CatalogoItem) {
  emit('update:modelValue', item.Value)
  emit('select', item)
  keyword.value = `${item.Value} — ${item.Name}`
  results.value = []
  showDropdown.value = false
}

function onBlur() {
  setTimeout(() => (showDropdown.value = false), 150)
}

const inputClass =
  'p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 transition-all bg-white font-mono text-sm'
</script>

<template>
  <div class="relative">
    <input
      v-model="keyword"
      type="text"
      :class="inputClass"
      :placeholder="placeholder ?? 'Busca por clave o descripción…'"
      @focus="showDropdown = results.length > 0"
      @blur="onBlur"
    />
    <div v-if="isSearching" class="absolute right-3 top-3 text-xs text-slate-400">Buscando…</div>
    <ul
      v-if="showDropdown"
      class="absolute z-30 w-full bg-white border border-slate-200 mt-1 shadow-xl rounded-lg max-h-56 overflow-y-auto"
    >
      <li
        v-for="r in results"
        :key="r.Value"
        class="p-2 hover:bg-emerald-50 cursor-pointer border-b border-slate-100 last:border-0"
        @mousedown.prevent="onSelect(r)"
      >
        <span class="font-mono text-emerald-700 font-bold bg-emerald-100 px-2 py-0.5 rounded text-xs mr-2">{{
          r.Value
        }}</span>
        <span class="text-slate-700 text-sm">{{ r.Name }}</span>
      </li>
    </ul>
  </div>
</template>
