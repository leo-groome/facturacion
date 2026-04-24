import { ref } from 'vue'

export type ToastVariant = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  message: string
  variant: ToastVariant
}

const toasts = ref<Toast[]>([])
let nextId = 1

function push(message: string, variant: ToastVariant, duration = 4000) {
  const id = nextId++
  toasts.value.push({ id, message, variant })
  setTimeout(() => dismiss(id), duration)
}

function dismiss(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

export function useToast() {
  return {
    toasts,
    success: (msg: string) => push(msg, 'success'),
    error: (msg: string) => push(msg, 'error', 6000),
    info: (msg: string) => push(msg, 'info'),
    dismiss,
  }
}
