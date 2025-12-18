import { useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export type Toast = {
  id: string
  message: string
  type: ToastType
  duration?: number
}

type ToastProps = {
  toast: Toast
  onClose: () => void
}

const ToastItem = ({ toast, onClose }: ToastProps) => {
  useEffect(() => {
    const duration = toast.duration ?? 4000
    if (duration > 0) {
      const timer = setTimeout(() => {
        setTimeout(onClose, 200) // Wait for exit animation
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [toast.duration, onClose])

  const styles = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    error: 'bg-rose-50 border-rose-200 text-rose-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 6, scale: 0.98 }}
      transition={{ duration: 0.15 }}
      className={`flex items-center gap-2 rounded-md border px-3 py-2 shadow-sm ${styles[toast.type]}`}
    >
      <p className="flex-1 text-sm font-medium leading-snug">{toast.message}</p>
      <button
        onClick={() => {
          setTimeout(onClose, 200)
        }}
        className="rounded px-1 text-sm leading-none text-current/70 transition-colors hover:bg-black/5 hover:text-current"
        aria-label="Close notification"
      >
        ✕
      </button>
    </motion.div>
  )
}

type ToastContainerProps = {
  toasts: Toast[]
  onClose: (id: string) => void
}

export const ToastContainer = ({ toasts, onClose }: ToastContainerProps) => {
  return (
    <div className="pointer-events-none fixed bottom-4 left-0 right-0 z-50 flex justify-center gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto max-w-sm">
            <ToastItem toast={toast} onClose={() => onClose(toast.id)} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  )
}

