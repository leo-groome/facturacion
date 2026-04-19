<script setup lang="ts">
import { ref, watch } from 'vue'
import { useFacturacionStore } from '@/stores/facturacion'
import api from '@/services/api'

const store = useFacturacionStore()
const searchKeyword = ref('')
const searchResults = ref<any[]>([])
const isSearching = ref(false)

const draftTotal = ref<number | null>(null)
const previewError = ref<string | null>(null)

// Campos del receptor
const receptorRazonSocial = ref('')
const receptorDomicilioFiscal = ref('')
const receptorEmail = ref('')

// Campos fiscales y de pago
const receptorRegimen = ref('')
const metodoPago = ref('PUE')
const formaPago = ref('01')
const moneda = ref('MXN')

const REGIMENES_FISCALES = [
  { value: '601', label: '601 - Régimen General de Ley Personas Morales' },
  { value: '602', label: '602 - Régimen Simplificado de Ley Personas Morales' },
  { value: '603', label: '603 - Personas Morales con Fines No Lucrativos' },
  { value: '604', label: '604 - Régimen de Pequeños Contribuyentes' },
  { value: '605', label: '605 - Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios' },
  { value: '606', label: '606 - Régimen de Arrendamiento' },
  { value: '607', label: '607 - Régimen de Enajenación o Adquisición de Bienes' },
  { value: '608', label: '608 - Régimen de los Demás Ingresos' },
  { value: '609', label: '609 - Régimen de Consolidación' },
  { value: '610', label: '610 - Régimen Residentes en el Extranjero sin Establecimiento Permanente en México' },
  { value: '611', label: '611 - Régimen de Ingresos por Dividendos (Socios y Accionistas)' },
  { value: '612', label: '612 - Régimen de las Personas Físicas con Actividades Empresariales y Profesionales' },
  { value: '613', label: '613 - Régimen Intermedio de las Personas Físicas con Actividades Empresariales' },
  { value: '614', label: '614 - Régimen de los Ingresos por Intereses' },
  { value: '615', label: '615 - Régimen de los Ingresos por Obtención de Premios' },
  { value: '616', label: '616 - Sin Obligaciones Fiscales' },
  { value: '617', label: '617 - PEMEX' },
  { value: '618', label: '618 - Régimen Simplificado de Ley Personas Físicas' },
  { value: '619', label: '619 - Ingresos por la Obtención de Préstamos' },
  { value: '620', label: '620 - Sociedades Cooperativas de Producción que Optan por Diferir sus Ingresos' },
  { value: '621', label: '621 - Régimen de Incorporación Fiscal' },
  { value: '622', label: '622 - Régimen de Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras PM' },
  { value: '623', label: '623 - Régimen Opcional para Grupos de Sociedades' },
  { value: '624', label: '624 - Régimen de los Coordinados' },
  { value: '625', label: '625 - Régimen de las Actividades Empresariales con Ingresos a través de Plataformas Tecnológicas' },
  { value: '626', label: '626 - Régimen Simplificado de Confianza' },
]

const FORMAS_PAGO = [
  { value: '01', label: '01 - Efectivo' },
  { value: '02', label: '02 - Cheque nominativo' },
  { value: '03', label: '03 - Transferencia electrónica de fondos' },
  { value: '04', label: '04 - Tarjeta de crédito' },
  { value: '28', label: '28 - Tarjeta de débito' },
  { value: '05', label: '05 - Monedero electrónico' },
  { value: '06', label: '06 - Dinero electrónico' },
  { value: '99', label: '99 - Por definir' },
]

const MONEDAS = [
  { value: 'MXN', label: 'MXN - Peso Mexicano' },
  { value: 'USD', label: 'USD - Dólar Americano' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'GBP', label: 'GBP - Libra Esterlina' },
  { value: 'CAD', label: 'CAD - Dólar Canadiense' },
  { value: 'JPY', label: 'JPY - Yen Japonés' },
]

// Predictivo con debounce
let debounceTimer: ReturnType<typeof setTimeout>
watch(searchKeyword, (newVal) => {
  clearTimeout(debounceTimer)
  if (newVal.length < 3) {
    searchResults.value = []
    return
  }

  debounceTimer = setTimeout(async () => {
    isSearching.value = true
    try {
      const response = await api.get(`/catalogos/prodserv?keyword=${newVal}`)
      searchResults.value = response.data.resultados
    } catch (e) {
      console.error('Error buscando catálogo SAT:', e)
    } finally {
      isSearching.value = false
    }
  }, 500)
})

const selectCatalog = (val: any) => {
  store.addConcepto({
    clave_prod_serv: val.Value,
    clave_unidad: 'H87',
    descripcion: val.Name,
    cantidad: 1,
    valor_unitario: 1000.00,
    importe: 1000.00,
    descuento: 0,
    impuestos: [
      { tipo: 'IVA', tasa: 0.160000, importe: 160.00 }
    ]
  })
  searchKeyword.value = ''
  searchResults.value = []
}

const previewFactura = async () => {
  previewError.value = null
  draftTotal.value = null

  if (!store.receptorRfc.trim()) {
    previewError.value = 'El RFC del receptor es obligatorio.'
    return
  }
  if (!receptorRazonSocial.value.trim()) {
    previewError.value = 'La razón social del receptor es obligatoria.'
    return
  }
  if (!receptorRegimen.value) {
    previewError.value = 'El régimen fiscal del receptor es obligatorio.'
    return
  }
  if (!receptorDomicilioFiscal.value.trim()) {
    previewError.value = 'El código postal del domicilio fiscal es obligatorio.'
    return
  }
  if (store.conceptos.length === 0) {
    previewError.value = 'Debes agregar al menos un concepto.'
    return
  }

  try {
    const draftPayload = {
      receptor_rfc: store.receptorRfc.toUpperCase().trim(),
      receptor_razon_social: receptorRazonSocial.value.trim(),
      receptor_regimen: receptorRegimen.value,
      receptor_domicilio_fiscal: receptorDomicilioFiscal.value.trim(),
      receptor_email: receptorEmail.value.trim() || undefined,
      uso_cfdi: 'G03',
      moneda: moneda.value,
      forma_pago: formaPago.value,
      metodo_pago: metodoPago.value,
      conceptos: store.conceptos
    }
    const { data } = await api.post('/facturacion/preview', draftPayload)
    draftTotal.value = data.total
  } catch (error: any) {
    previewError.value = 'Error al simular: ' + (error.response?.data?.detail || error.message)
  }
}

const selectClass = 'p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition-all bg-slate-50 appearance-none cursor-pointer'
const inputClass = 'p-3 w-full border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition-all bg-slate-50'
</script>

<template>
  <div class="smart-form bg-white shadow-xl rounded-xl p-8 border border-slate-100">
    <h2 class="text-2xl font-black mb-6 text-slate-800 tracking-tight">Generador de CFDI 4.0</h2>

    <!-- Datos del Receptor -->
    <div class="mb-6">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Datos del Receptor</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">RFC Receptor <span class="text-red-500">*</span></label>
          <input v-model="store.receptorRfc" type="text" :class="inputClass" placeholder="XAXX010101000" maxlength="13" style="text-transform:uppercase" />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Razón Social <span class="text-red-500">*</span></label>
          <input v-model="receptorRazonSocial" type="text" :class="inputClass" placeholder="Nombre o empresa del receptor" />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Régimen Fiscal SAT <span class="text-red-500">*</span></label>
          <select v-model="receptorRegimen" :class="selectClass">
            <option value="" disabled>Selecciona un régimen fiscal…</option>
            <option v-for="r in REGIMENES_FISCALES" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">C.P. Domicilio Fiscal <span class="text-red-500">*</span></label>
          <input v-model="receptorDomicilioFiscal" type="text" :class="inputClass" placeholder="Ej. 06600" maxlength="5" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-semibold text-slate-700 mb-2">Correo Electrónico del Receptor</label>
          <input v-model="receptorEmail" type="email" :class="inputClass" placeholder="receptor@empresa.com" />
        </div>
      </div>
    </div>

    <!-- Condiciones de Pago -->
    <div class="mb-6">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Condiciones de Pago</h3>
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Método de Pago <span class="text-red-500">*</span></label>
          <select v-model="metodoPago" :class="selectClass">
            <option value="PUE">PUE - Pago en una sola exhibición</option>
            <option value="PPD">PPD - Pago en parcialidades o diferido</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Forma de Pago <span class="text-red-500">*</span></label>
          <select v-model="formaPago" :class="selectClass">
            <option v-for="f in FORMAS_PAGO" :key="f.value" :value="f.value">{{ f.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-2">Moneda <span class="text-red-500">*</span></label>
          <select v-model="moneda" :class="selectClass">
            <option v-for="m in MONEDAS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Conceptos -->
    <div class="mb-8">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Conceptos (Partidas)</h3>
      <div class="relative mb-4">
        <label class="block text-sm font-semibold text-slate-700 mb-2">Buscador Predictivo SAT</label>
        <input v-model="searchKeyword" type="text" :class="inputClass + ' focus:ring-emerald-500'" placeholder="Buscar por Producto o Servicio (Ej. Computadoras...)" />
        <ul v-if="searchResults.length" class="absolute z-20 w-full bg-white border border-slate-200 mt-2 shadow-2xl rounded-lg max-h-56 overflow-y-auto hidden-scrollbar">
          <li v-for="res in searchResults" :key="res.Value" @click="selectCatalog(res)" class="p-3 hover:bg-emerald-50 cursor-pointer border-b border-slate-100 last:border-0 transition-colors">
            <span class="font-mono text-emerald-700 font-bold bg-emerald-100 px-2 py-1 rounded text-xs mr-2">{{res.Value}}</span>
            <span class="text-slate-700">{{res.Name}}</span>
          </li>
        </ul>
        <div v-if="isSearching" class="text-xs text-slate-500 mt-2 flex items-center gap-2">
          <svg class="animate-spin h-4 w-4 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          Buscando en catálogos del SAT...
        </div>
      </div>

      <div v-if="store.conceptos.length" class="space-y-3">
        <div v-for="(concepto, idx) in store.conceptos" :key="idx" class="p-4 bg-slate-50 rounded-lg border border-slate-200 flex justify-between items-center group">
          <div>
            <div class="font-semibold text-slate-800">{{ concepto.descripcion }}</div>
            <div class="text-xs text-slate-400 font-mono mt-0.5">{{ concepto.clave_prod_serv }}</div>
            <div class="text-sm text-slate-500 mt-1">{{ concepto.cantidad }} x ${{ concepto.valor_unitario.toFixed(2) }}</div>
          </div>
          <button @click="store.removeConcepto(idx)" class="text-red-500 hover:text-red-700 font-bold opacity-0 group-hover:opacity-100 transition-opacity">Eliminar</button>
        </div>
      </div>
    </div>

    <!-- Totales -->
    <div class="bg-gradient-to-br from-slate-50 to-slate-100 p-6 rounded-xl mb-8 border border-slate-200">
      <div class="text-right space-y-3">
        <p class="text-sm font-semibold text-slate-500 flex justify-end gap-6"><span>Subtotal:</span> <span class="text-slate-800 w-28">${{ store.subtotal.toFixed(2) }} {{ moneda }}</span></p>
        <p class="text-sm font-semibold text-slate-500 flex justify-end gap-6"><span>IVA/IEPS Trasladados:</span> <span class="text-slate-800 w-28">${{ store.totalImpuestosTrasladados.toFixed(2) }}</span></p>
        <div class="w-full h-px bg-slate-200 my-2"></div>
        <p class="text-2xl font-black text-slate-900 flex justify-end gap-6 items-center"><span class="text-sm font-semibold text-slate-500 pb-1">Total {{ moneda }}:</span> <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-teal-500">${{ store.total.toFixed(2) }}</span></p>
      </div>
    </div>

    <div v-if="previewError" class="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-4 py-3 rounded-lg">
      {{ previewError }}
    </div>
    <div v-if="draftTotal !== null" class="mb-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-bold px-4 py-3 rounded-lg">
      Borrador validado sin timbrar. Total {{ moneda }}: ${{ Number(draftTotal).toFixed(2) }}
    </div>

    <button @click="previewFactura" class="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-md hover:shadow-lg flex justify-center items-center gap-2 disabled:opacity-50" :disabled="!store.conceptos.length">
      Generar Vista Previa (Simulador)
    </button>
  </div>
</template>
