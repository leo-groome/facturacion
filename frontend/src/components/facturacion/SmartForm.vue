<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useFacturacionStore } from '@/stores/facturacion'
import { recalcularConcepto, type Concepto, type ObjetoImp } from '@/utils/calculoCfdi'
import api from '@/services/api'
import CatalogoSearch from './CatalogoSearch.vue'
import ConceptoEditor from './ConceptoEditor.vue'

const store = useFacturacionStore()

const draftTotal = ref<number | null>(null)
const previewError = ref<string | null>(null)
const emisorError = ref<string | null>(null)

// Campos del receptor
const receptorRazonSocial = ref('')
const receptorDomicilioFiscal = ref('')
const receptorEmail = ref('')

// Campos fiscales y de pago
const receptorRegimen = ref('')
const metodoPago = ref<'PUE' | 'PPD'>('PUE')
const formaPago = ref('01')
const moneda = ref('MXN')
const enviarPorEmail = ref(false)
const usoCfdi = ref('G03')
const usosCfdiOptions = ref<{ Value: string; Name: string }[]>([])

// Regla SAT: PPD obliga FormaPago=99 (Por definir)
watch(metodoPago, (m) => {
  if (m === 'PPD') formaPago.value = '99'
  else if (formaPago.value === '99') formaPago.value = '01'
})

// Al cambiar régimen del receptor, recargar usos CFDI permitidos
watch(receptorRegimen, async (r) => {
  if (!r) {
    usosCfdiOptions.value = []
    return
  }
  try {
    const { data } = await api.get('/catalogos/usos-cfdi', { params: { regimen: r } })
    usosCfdiOptions.value = data.resultados || []
    if (!usosCfdiOptions.value.some((u) => u.Value === usoCfdi.value)) {
      usoCfdi.value = usosCfdiOptions.value[0]?.Value || ''
    }
  } catch {
    usosCfdiOptions.value = []
  }
})

const REGIMENES_FISCALES = [
  { value: '601', label: '601 - Régimen General de Ley Personas Morales' },
  { value: '603', label: '603 - Personas Morales con Fines No Lucrativos' },
  { value: '605', label: '605 - Sueldos y Salarios' },
  { value: '606', label: '606 - Arrendamiento' },
  { value: '612', label: '612 - Personas Físicas con Actividades Empresariales y Profesionales' },
  { value: '616', label: '616 - Sin Obligaciones Fiscales' },
  { value: '621', label: '621 - Régimen de Incorporación Fiscal' },
  { value: '626', label: '626 - Régimen Simplificado de Confianza' },
]

const FORMAS_PAGO = [
  { value: '01', label: '01 - Efectivo' },
  { value: '02', label: '02 - Cheque nominativo' },
  { value: '03', label: '03 - Transferencia electrónica de fondos' },
  { value: '04', label: '04 - Tarjeta de crédito' },
  { value: '28', label: '28 - Tarjeta de débito' },
  { value: '99', label: '99 - Por definir (PPD)' },
]

const MONEDAS = [
  { value: 'MXN', label: 'MXN - Peso Mexicano' },
  { value: 'USD', label: 'USD - Dólar Americano' },
  { value: 'EUR', label: 'EUR - Euro' },
]

onMounted(async () => {
  try {
    await store.cargarEmisor()
  } catch {
    emisorError.value =
      'No se encontró un CSD registrado. Ve a /onboarding y sube tu certificado antes de facturar.'
  }
})

// Al cambiar RFC del receptor o régimen del emisor, recalcular TODOS los conceptos
watch(
  () => [store.receptorRfc, store.emisorRegimen],
  () => {
    store.conceptos.forEach((c, i) => {
      store.updateConcepto(
        i,
        recalcularConcepto(c, {
          emisorRegimen: store.emisorRegimen,
          receptorRfc: store.receptorRfc,
        }),
      )
    })
  },
)

function agregarPartida(item: { Value: string; Name: string }) {
  const nuevo: Concepto = {
    clave_prod_serv: item.Value,
    clave_unidad: 'H87',
    descripcion: item.Name,
    cantidad: 1,
    valor_unitario: 0,
    importe: 0,
    descuento: 0,
    objeto_imp: '02' as ObjetoImp,
    impuestos: [],
  }
  store.addConcepto(
    recalcularConcepto(nuevo, {
      emisorRegimen: store.emisorRegimen,
      receptorRfc: store.receptorRfc,
    }),
  )
}

function agregarPartidaVacia() {
  const nuevo: Concepto = {
    clave_prod_serv: '',
    clave_unidad: 'H87',
    descripcion: '',
    cantidad: 1,
    valor_unitario: 0,
    importe: 0,
    descuento: 0,
    objeto_imp: '02' as ObjetoImp,
    impuestos: [],
  }
  store.addConcepto(nuevo)
}

const previewFactura = async () => {
  previewError.value = null
  draftTotal.value = null

  if (!store.receptorRfc.trim()) return (previewError.value = 'El RFC del receptor es obligatorio.')
  if (!receptorRazonSocial.value.trim()) return (previewError.value = 'La razón social del receptor es obligatoria.')
  if (!receptorRegimen.value) return (previewError.value = 'El régimen fiscal del receptor es obligatorio.')
  if (!receptorDomicilioFiscal.value.trim()) return (previewError.value = 'El C.P. es obligatorio.')
  if (store.conceptos.length === 0) return (previewError.value = 'Debes agregar al menos un concepto.')
  if (enviarPorEmail.value && !receptorEmail.value.trim()) {
    previewError.value = 'Para enviar por email necesitas capturar el correo del receptor.'
    return
  }

  for (const c of store.conceptos) {
    if (!c.clave_prod_serv || !c.descripcion || c.cantidad <= 0 || c.valor_unitario <= 0) {
      previewError.value = 'Cada concepto requiere clave, descripción, cantidad y precio > 0.'
      return
    }
  }

  try {
    const draftPayload = {
      receptor_rfc: store.receptorRfc.toUpperCase().trim(),
      receptor_razon_social: receptorRazonSocial.value.trim(),
      receptor_regimen: receptorRegimen.value,
      receptor_domicilio_fiscal: receptorDomicilioFiscal.value.trim(),
      receptor_email: receptorEmail.value.trim() || undefined,
      uso_cfdi: usoCfdi.value,
      moneda: moneda.value,
      forma_pago: formaPago.value,
      metodo_pago: metodoPago.value,
      enviar_por_email: enviarPorEmail.value,
      conceptos: store.conceptos,
    }
    const { data } = await api.post('/facturacion/preview', draftPayload)
    draftTotal.value = data.total
  } catch (error: any) {
    previewError.value = 'Error al simular: ' + (error.response?.data?.detail || error.message)
  }
}

const selectClass =
  'p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition-all bg-slate-50 appearance-none cursor-pointer'
const inputClass =
  'p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition-all bg-slate-50'
</script>

<template>
  <div class="smart-form bg-white shadow-xl rounded-xl p-8 border border-slate-100">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-black text-slate-800 tracking-tight">Generador de CFDI 4.0</h2>
      <span
        v-if="store.emisorRegimen"
        class="text-xs font-mono px-3 py-1 rounded-full"
        :class="store.esResico ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'"
      >
        Emisor: {{ store.emisorRfc }} · Régimen {{ store.emisorRegimen }}
        <template v-if="store.esResico"> (RESICO) </template>
      </span>
    </div>

    <div
      v-if="emisorError"
      class="mb-6 bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-4 py-3 rounded-lg"
    >
      {{ emisorError }}
    </div>

    <!-- Datos del Receptor -->
    <div class="mb-6">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Datos del Receptor</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2"
            >RFC Receptor <span class="text-red-500">*</span></label
          >
          <input
            v-model="store.receptorRfc"
            type="text"
            :class="inputClass"
            placeholder="XAXX010101000"
            maxlength="13"
            style="text-transform: uppercase"
          />
          <p v-if="store.receptorRfc" class="text-xs mt-1 text-slate-500">
            {{ store.receptorRfc.length === 12 ? 'Persona Moral' : store.receptorRfc.length === 13 ? 'Persona Física' : '' }}
          </p>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2"
            >Razón Social <span class="text-red-500">*</span></label
          >
          <input
            v-model="receptorRazonSocial"
            type="text"
            :class="inputClass"
            placeholder="Nombre o empresa del receptor"
          />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2"
            >Régimen Fiscal SAT <span class="text-red-500">*</span></label
          >
          <select v-model="receptorRegimen" :class="selectClass">
            <option value="" disabled>Selecciona un régimen fiscal…</option>
            <option v-for="r in REGIMENES_FISCALES" :key="r.value" :value="r.value">
              {{ r.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2"
            >C.P. Domicilio Fiscal <span class="text-red-500">*</span></label
          >
          <input
            v-model="receptorDomicilioFiscal"
            type="text"
            :class="inputClass"
            placeholder="Ej. 06600"
            maxlength="5"
          />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2"
            >Uso CFDI <span class="text-red-500">*</span></label
          >
          <select v-model="usoCfdi" :class="selectClass" :disabled="!usosCfdiOptions.length">
            <option value="" disabled>
              {{ receptorRegimen ? 'Selecciona un uso…' : 'Selecciona régimen primero' }}
            </option>
            <option v-for="u in usosCfdiOptions" :key="u.Value" :value="u.Value">
              {{ u.Value }} - {{ u.Name }}
            </option>
          </select>
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-semibold text-slate-700 mb-2">Correo Electrónico del Receptor</label>
          <input v-model="receptorEmail" type="email" :class="inputClass" placeholder="receptor@empresa.com" />
          <label class="flex items-center gap-2 mt-2 text-sm text-slate-600 cursor-pointer">
            <input v-model="enviarPorEmail" type="checkbox" class="rounded border-slate-300" />
            Enviar CFDI al receptor por email después de timbrar
          </label>
        </div>
      </div>
    </div>

    <!-- Condiciones de Pago -->
    <div class="mb-6">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Condiciones de Pago</h3>
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Método de Pago</label>
          <select v-model="metodoPago" :class="selectClass">
            <option value="PUE">PUE - Pago en una sola exhibición</option>
            <option value="PPD">PPD - Pago en parcialidades o diferido</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Forma de Pago</label>
          <select
            v-model="formaPago"
            :class="selectClass"
            :disabled="metodoPago === 'PPD'"
          >
            <option
              v-for="f in FORMAS_PAGO.filter((x) => metodoPago !== 'PPD' || x.value === '99')"
              :key="f.value"
              :value="f.value"
            >
              {{ f.label }}
            </option>
          </select>
          <p v-if="metodoPago === 'PPD'" class="text-xs mt-1 text-amber-700">
            PPD requiere forma de pago 99 (Por definir).
          </p>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Moneda</label>
          <select v-model="moneda" :class="selectClass">
            <option v-for="m in MONEDAS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Conceptos -->
    <div class="mb-8">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400">Conceptos (Partidas)</h3>
        <button
          class="text-xs font-bold text-emerald-700 hover:text-emerald-900 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1"
          @click="agregarPartidaVacia"
        >
          + Partida en blanco
        </button>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-semibold text-slate-700 mb-2">Buscar producto/servicio SAT y agregar</label>
        <CatalogoSearch
          endpoint="prodserv"
          model-value=""
          placeholder="Ej. Café, Servicios de consultoría…"
          @select="agregarPartida"
        />
      </div>

      <div v-if="store.conceptos.length" class="space-y-4">
        <ConceptoEditor
          v-for="(c, i) in store.conceptos"
          :key="i"
          :model-value="c"
          :index="i"
          :emisor-regimen="store.emisorRegimen"
          :receptor-rfc="store.receptorRfc"
          @update:model-value="(v) => store.updateConcepto(i, v)"
          @remove="store.removeConcepto(i)"
        />
      </div>
      <p v-else class="text-sm text-slate-400 italic">Aún no has agregado partidas.</p>
    </div>

    <!-- Totales -->
    <div class="bg-gradient-to-br from-slate-50 to-slate-100 p-6 rounded-xl mb-6 border border-slate-200">
      <div class="text-right space-y-2">
        <p class="text-sm font-semibold text-slate-500 flex justify-end gap-6">
          <span>Subtotal:</span> <span class="text-slate-800 w-32">${{ store.subtotal.toFixed(2) }} {{ moneda }}</span>
        </p>
        <p class="text-sm font-semibold text-emerald-700 flex justify-end gap-6">
          <span>+ Traslados (IVA/IEPS):</span>
          <span class="w-32">${{ store.totalImpuestosTrasladados.toFixed(2) }}</span>
        </p>
        <p class="text-sm font-semibold text-red-600 flex justify-end gap-6">
          <span>− Retenciones (ISR/IVA):</span>
          <span class="w-32">${{ store.totalImpuestosRetenidos.toFixed(2) }}</span>
        </p>
        <div
          v-if="store.retencionResicoISR > 0"
          class="flex justify-end"
        >
          <span
            class="text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 rounded-full px-3 py-1"
          >
            Retención ISR 1.25% aplicada (RESICO → Persona Moral): ${{ store.retencionResicoISR.toFixed(2) }}
          </span>
        </div>
        <div class="w-full h-px bg-slate-200 my-2"></div>
        <p class="text-2xl font-black text-slate-900 flex justify-end gap-6 items-center">
          <span class="text-sm font-semibold text-slate-500 pb-1">Total {{ moneda }}:</span>
          <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-teal-500"
            >${{ store.total.toFixed(2) }}</span
          >
        </p>
      </div>
    </div>

    <div
      v-if="previewError"
      class="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-4 py-3 rounded-lg"
    >
      {{ previewError }}
    </div>
    <div
      v-if="draftTotal !== null"
      class="mb-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-bold px-4 py-3 rounded-lg"
    >
      Borrador validado sin timbrar. Total {{ moneda }}: ${{ Number(draftTotal).toFixed(2) }}
    </div>

    <button
      class="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-md hover:shadow-lg disabled:opacity-50"
      :disabled="!store.conceptos.length"
      @click="previewFactura"
    >
      Generar Vista Previa (Simulador)
    </button>
  </div>
</template>
