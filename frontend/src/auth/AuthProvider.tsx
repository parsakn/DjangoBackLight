import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { PropsWithChildren } from 'react'
import { authApi, clearAuthTokens, getAccessToken, getRefreshToken, setAuthTokens } from '../api/http'
import type { TokenObtainPair, UserCreate } from '../api/types'

type AuthContextValue = {
  accessToken: string | null
  refreshToken: string | null
  username: string | null
  isBootstrapping: boolean
  isAuthenticated: boolean
  login: (payload: Pick<TokenObtainPair, 'username' | 'password'>) => Promise<void>
  register: (payload: UserCreate) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState<string | null>(null)
  const [username, setUsername] = useState<string | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  useEffect(() => {
    const storedAccess = getAccessToken()
    const storedRefresh = getRefreshToken()
    if (storedAccess) setAccessToken(storedAccess)
    if (storedRefresh) setRefreshToken(storedRefresh)
    setIsBootstrapping(false)
  }, [])

  const login = async (payload: Pick<TokenObtainPair, 'username' | 'password'>) => {
    const res = await authApi.login(payload)
    if (res.access) setAccessToken(res.access)
    if (res.refresh) setRefreshToken(res.refresh)
    setAuthTokens(res.access, res.refresh)
    setUsername(payload.username)
  }

  const register = async (payload: UserCreate) => {
    await authApi.register(payload)
    await login({ username: payload.username, password: payload.password })
  }

  const logout = () => {
    clearAuthTokens()
    setAccessToken(null)
    setRefreshToken(null)
    setUsername(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      refreshToken,
      username,
      isBootstrapping,
      isAuthenticated: Boolean(accessToken || refreshToken),
      login,
      register,
      logout,
    }),
    [accessToken, refreshToken, username, isBootstrapping],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

