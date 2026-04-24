<script setup lang="ts">
import { computed, watch } from 'vue'
import CatalogoSearch from './CatalogoSearch.vue'
import {
  recalcularConcepto,
  totalConcepto,
  type Concepto,
  type ObjetoImp,
} from '@/utils/calculoCfdi'

const props = defineProps<{
  modelValue: Concepto
  emisorRegimen: string
  receptorRfc: string
  index: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: Concepto): void
  (e: 'remove'): void
}>()

function update(partial: Partial<Concepto>) {
  const merged: Concepto = { ...props.modelValue, ...partial }
  const recalculado = recalcularConcepto(merged, {
    emisorRegimen: props.emisorRegimen,
    receptorRfc: props.receptorRfc,
  })
  emit('update:modelValue', recalculado)
}

// Recalcular al cambiar contexto fiscal (régimen emisor o RFC receptor)
watch(
  () => [props.emisorRegimen, props.receptorRfc],
  () => {
    const recalculado = recalcularConcepto(props.modelValue, {
      emisorRegimen: props.emisorRegimen,
      receptorRfc: props.receptorRfc,
    })
    emit('update:modelValue', recalculado)
  },
)

const total = computed(() => totalConcepto(props.modelValue))

const OBJETO_IMP_OPCIONES: { value: ObjetoImp; label: string }[] = [
  { value: '01', label: '01 — No objeto de impuesto' },
  { value: '02', label: '02 — Sí objeto de impuesto' },
  { value: '03', label: '03 — Sí objeto y no obligado al desglose' },
  { value: '04', label: '04 — Sí objeto y no causa impuesto' },
]

const IVA_OPCIONES = [
  { value: 0.16, label: 'IVA 16% (general)' },
  { value: 0.08, label: 'IVA 8% (frontera)' },
  { value: 0, label: 'IVA 0% (tasa cero)' },
]

// Tasas IEPS más comunes según Ley del IEPS (ad valorem).
// Cuotas fijas (gasolina, bebidas azucaradas) no están soportadas aquí.
const IEPS_OPCIONES = [
  { value: 0.08, label: '8% (alimentos no básicos con alta densidad calórica)' },
  { value: 0.25, label: '25% (bebidas energizantes)' },
  { value: 0.265, label: '26.5% (bebidas alcohólicas ≤14°GL)' },
  { value: 0.30, label: '30% (bebidas alcohólicas >14° y ≤20°GL)' },
  { value: 0.53, label: '53% (bebidas alcohólicas >20°GL / tabacos)' },
  { value: 1.60, label: '160% (tabacos labrados cigarros)' },
]

const IVA_RET_OPCIONES = [
  { value: 0.106667, label: '10.6667% (2/3 de 16% — servicios profesionales PF→PM)' },
  { value: 0.04, label: '4% (autotransporte de carga)' },
  { value: 0.06, label: '6% (prestación de servicios — outsourcing 1-A frac. IV)' },
  { value: 0.16, label: '16% (IVA retenido total)' },
]

const inputCls =
  'p-2 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 transition-all bg-white text-sm'
const labelCls = 'block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1'
</script>

<template>
  <div class="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-3">
    <div class="flex justify-between items-start">
      <span class="text-xs font-bold uppercase tracking-widest text-slate-400">
        Partida #{{ index + 1 }}
      </span>
      <button
        class="text-red-500 hover:text-red-700 text-xs font-bold"
        @click="emit('remove')"
      >
        Eliminar
      </button>
    </div>

    <div class="grid grid-cols-12 gap-3">
      <div class="col-span-12">
        <label :class="labelCls">Clave ProdServ (SAT)</label>
        <CatalogoSearch
          endpoint="prodserv"
          :model-value="modelValue.clave_prod_serv"
          placeholder="Busca un producto o servicio…"
          @select="(item) => update({ clave_prod_serv: item.Value, descripcion: modelValue.descripcion || item.Name })"
        />
        <p v-if="modelValue.clave_prod_serv" class="text-xs text-slate-500 mt-1 font-mono">
          Clave actual: {{ modelValue.clave_prod_serv }}
        </p>
      </div>

      <div class="col-span-8">
        <label :class="labelCls">Descripción</label>
        <input
          :class="inputCls"
          :value="modelValue.descripcion"
          @input="(e) => update({ descripcion: (e.target as HTMLInputElement).value })"
        />
      </div>

      <div class="col-span-4">
        <label :class="labelCls">Clave Unidad</label>
        <CatalogoSearch
          endpoint="unidades"
          :model-value="modelValue.clave_unidad"
          placeholder="H87, KGM…"
          @select="(item) => update({ clave_unidad: item.Value })"
        />
        <p class="text-xs text-slate-500 mt-1 font-mono">Actual: {{ modelValue.clave_unidad }}</p>
      </div>

      <div class="col-span-3">
        <label :class="labelCls">Cantidad</label>
        <input
          type="number"
          step="0.000001"
          min="0"
          :class="inputCls"
          :value="modelValue.cantidad"
          @input="(e) => update({ cantidad: parseFloat((e.target as HTMLInputElement).value) || 0 })"
        />
      </div>
      <div class="col-span-3">
        <label :class="labelCls">Valor unitario</label>
        <input
          type="number"
          step="0.01"
          min="0"
          :class="inputCls"
          :value="modelValue.valor_unitario"
          @input="(e) => update({ valor_unitario: parseFloat((e.target as HTMLInputElement).value) || 0 })"
        />
      </div>
      <div class="col-span-3">
        <label :class="labelCls">Descuento</label>
        <input
          type="number"
          step="0.01"
          min="0"
          :class="inputCls"
          :value="modelValue.descuento"
          @input="(e) => update({ descuento: parseFloat((e.target as HTMLInputElement).value) || 0 })"
        />
      </div>
      <div class="col-span-3">
        <label :class="labelCls">Objeto Imp.</label>
        <select
          :class="inputCls + ' appearance-none cursor-pointer'"
          :value="modelValue.objeto_imp"
          @change="(e) => update({ objeto_imp: (e.target as HTMLSelectElement).value as ObjetoImp })"
        >
          <option v-for="o in OBJETO_IMP_OPCIONES" :key="o.value" :value="o.value">
            {{ o.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Configuración de impuestos aplicables al concepto -->
    <div
      v-if="modelValue.objeto_imp === '02'"
      class="border border-slate-200 rounded-lg p-3 space-y-3 bg-slate-50"
    >
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">
        Impuestos aplicables
      </p>

      <div class="grid grid-cols-12 gap-3">
        <!-- IVA tasa -->
        <div class="col-span-4">
          <label :class="labelCls">IVA</label>
          <select
            :class="inputCls + ' appearance-none cursor-pointer'"
            :value="modelValue.iva_tasa ?? 0.16"
            @change="(e) => update({ iva_tasa: parseFloat((e.target as HTMLSelectElement).value) })"
          >
            <option v-for="o in IVA_OPCIONES" :key="o.value" :value="o.value">
              {{ o.label }}
            </option>
          </select>
        </div>

        <!-- IEPS -->
        <div class="col-span-4">
          <label :class="labelCls">IEPS (opcional)</label>
          <div class="flex gap-2 items-center">
            <input
              type="checkbox"
              :checked="!!modelValue.ieps_tasa"
              class="rounded border-slate-300"
              @change="(e) => update({ ieps_tasa: (e.target as HTMLInputElement).checked ? 0.08 : 0 })"
            />
            <select
              v-if="modelValue.ieps_tasa"
              :class="inputCls + ' appearance-none cursor-pointer'"
              :value="modelValue.ieps_tasa"
              @change="(e) => update({ ieps_tasa: parseFloat((e.target as HTMLSelectElement).value) })"
            >
              <option v-for="o in IEPS_OPCIONES" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
            <span v-else class="text-xs text-slate-400">Sin IEPS</span>
          </div>
          <p v-if="modelValue.ieps_tasa" class="text-xs text-amber-700 mt-1">
            Confirma la tasa aplicable según la Ley del IEPS.
          </p>
        </div>

        <!-- Retención IVA -->
        <div class="col-span-4">
          <label :class="labelCls">Retención IVA (opcional)</label>
          <div class="flex gap-2 items-center">
            <input
              type="checkbox"
              :checked="!!modelValue.iva_ret_tasa"
              class="rounded border-slate-300"
              @change="(e) => update({ iva_ret_tasa: (e.target as HTMLInputElement).checked ? 0.106667 : 0 })"
            />
            <select
              v-if="modelValue.iva_ret_tasa"
              :class="inputCls + ' appearance-none cursor-pointer'"
              :value="modelValue.iva_ret_tasa"
              @change="(e) => update({ iva_ret_tasa: parseFloat((e.target as HTMLSelectElement).value) })"
            >
              <option v-for="o in IVA_RET_OPCIONES" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
            <span v-else class="text-xs text-slate-400">Sin retención</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Desglose de impuestos calculados -->
    <div v-if="modelValue.impuestos.length" class="bg-slate-50 rounded-lg p-3 text-xs space-y-1">
      <div
        v-for="(imp, i) in modelValue.impuestos"
        :key="i"
        class="flex justify-between font-mono"
      >
        <span :class="imp.es_retencion ? 'text-red-600' : 'text-emerald-700'">
          {{ imp.es_retencion ? '− Retención' : '+ Traslado' }} {{ imp.tipo }}
          ({{ (imp.tasa * 100).toFixed(2) }}% sobre base {{ imp.base.toFixed(2) }})
        </span>
        <span class="font-bold">${{ imp.importe.toFixed(6) }}</span>
      </div>
    </div>
    <div
      v-else-if="modelValue.objeto_imp === '02'"
      class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2"
    >
      ObjetoImp = 02 requiere impuestos. Verifica cantidad y precio para generar IVA.
    </div>

    <div class="flex justify-between items-center pt-2 border-t border-slate-100">
      <span class="text-xs text-slate-500">Importe: ${{ modelValue.importe.toFixed(2) }}</span>
      <span class="text-sm font-black text-slate-800">Total partida: ${{ total.toFixed(2) }}</span>
    </div>
  </div>
</template>
