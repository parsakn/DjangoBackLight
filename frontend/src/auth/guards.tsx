import { Navigate } from 'react-router-dom'
import type { PropsWithChildren } from 'react'
import { useAuth } from './AuthProvider'

type GuardProps = PropsWithChildren<{ redirectTo?: string }>

export const ProtectedRoute = ({ children, redirectTo = '/login' }: GuardProps) => {
  const { isAuthenticated, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Checking session...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  return children
}

export const PublicOnly = ({ children, redirectTo = '/' }: GuardProps) => {
  const { isAuthenticated, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Loading...
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  return children
}

