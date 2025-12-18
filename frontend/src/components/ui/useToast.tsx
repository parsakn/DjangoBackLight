import { createContext, useContext, useState, useCallback } from 'react'
import type { Toast, ToastType } from './Toast'

type ToastContextValue = {
  toast: (message: string, type?: ToastType, duration?: number) => void
  success: (message: string, duration?: number) => void
  error: (message: string, duration?: number) => void
  warning: (message: string, duration?: number) => void
  info: (message: string, duration?: number) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

type ToastProviderProps = {
  children: React.ReactNode
  onToast: (toast: Toast) => void
}

export const ToastProvider = ({ children, onToast }: ToastProviderProps) => {
  const showToast = useCallback(
    (message: string, type: ToastType = 'info', duration?: number) => {
      const id = `${Date.now()}-${Math.random()}`
      onToast({ id, message, type, duration })
    },
    [onToast],
  )

  const value: ToastContextValue = {
    toast: showToast,
    success: (message, duration) => showToast(message, 'success', duration),
    error: (message, duration) => showToast(message, 'error', duration),
    warning: (message, duration) => showToast(message, 'warning', duration),
    info: (message, duration) => showToast(message, 'info', duration),
  }

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
}

