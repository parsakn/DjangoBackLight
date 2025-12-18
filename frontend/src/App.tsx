import { useState, useCallback } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute, PublicOnly } from './auth/guards'
import { LoginPage } from './features/auth/Login'
import { RegisterPage } from './features/auth/Register'
import { DashboardPage } from './features/dashboard/Dashboard'
import { ToastProvider } from './components/ui/useToast'
import { ToastContainer } from './components/ui/Toast'
import type { Toast } from './components/ui/Toast'

function App() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Toast) => {
    setToasts((prev) => [...prev, toast])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastProvider onToast={addToast}>
      <AuthProvider>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicOnly>
                <LoginPage />
              </PublicOnly>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnly>
                <RegisterPage />
              </PublicOnly>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <ToastContainer toasts={toasts} onClose={removeToast} />
      </AuthProvider>
    </ToastProvider>
  )
}

export default App
