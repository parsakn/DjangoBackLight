import type { PropsWithChildren } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from './Button'

type ModalProps = PropsWithChildren<{
  open: boolean
  title: string
  onClose: () => void
  description?: string
}> &
  React.HTMLAttributes<HTMLDivElement>

export const Modal = ({ open, onClose, title, description, children }: ModalProps) => {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-xl"
            initial={{ scale: 0.96, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.96, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
                {description && <p className="text-sm text-slate-600">{description}</p>}
              </div>
              <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close dialog">
                Close
              </Button>
            </div>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

