import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  HomePost,
  HomeView,
  LampPost,
  LampStatusUpdate,
  LampView,
  RoomPost,
  RoomView,
  TokenObtainPair,
  TokenRefresh,
  UserCreate,
  VoiceCommandResult,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const storageKeys = {
  access: 'smartlight:access',
  refresh: 'smartlight:refresh',
}

let accessTokenMemory: string | null = null

const readStorage = (key: string) => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(key)
}

const writeStorage = (key: string, value: string | null) => {
  if (typeof window === 'undefined') return
  if (!value) {
    localStorage.removeItem(key)
    return
  }
  localStorage.setItem(key, value)
}

export const getAccessToken = () =>
  accessTokenMemory || readStorage(storageKeys.access) || null

export const getRefreshToken = () => readStorage(storageKeys.refresh) || null

export const setAuthTokens = (access?: string, refresh?: string) => {
  accessTokenMemory = access ?? null
  if (access) writeStorage(storageKeys.access, access)
  if (refresh) writeStorage(storageKeys.refresh, refresh)
}

export const clearAuthTokens = () => {
  accessTokenMemory = null
  writeStorage(storageKeys.access, null)
  writeStorage(storageKeys.refresh, null)
}

type RetryConfig = AxiosRequestConfig & { _retry?: boolean }

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
})

/**
 * Try to turn a backend/axios error into a human‑readable message.
 * Handles common DRF / Django validation error shapes.
 */
export const getApiErrorMessage = (error: unknown, fallback = 'Something went wrong') => {
  if (axios.isAxiosError(error)) {
    // Network / no response from server
    if (!error.response) {
      return 'Cannot reach the server. Please check your internet connection and try again.'
    }

    const data = error.response.data as Record<string, unknown>

    // Plain string response
    if (typeof data === 'string') {
      return data
    }

    // DRF-style {"detail": "..."}
    if (data?.detail) {
      if (typeof data.detail === 'string') return data.detail
      try {
        return JSON.stringify(data.detail)
      } catch {
        return fallback
      }
    }

    // Field errors: {"field": ["msg1", "msg2"], ...}
    if (data && typeof data === 'object') {
      const parts: string[] = []
      Object.entries(data).forEach(([field, value]) => {
        if (Array.isArray(value)) {
          parts.push(`${field}: ${value.join(', ')}`)
        } else if (typeof value === 'string') {
          parts.push(`${field}: ${value}`)
        }
      })
      if (parts.length) return parts.join(' | ')
    }

    return error.message || fallback
  }

  if (error instanceof Error) return error.message || fallback

  return fallback
}

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

const refreshAccessToken = async (): Promise<string | null> => {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const refresh = getRefreshToken()
    if (!refresh) return null
    try {
      const res = await axios.post<TokenRefresh>(
        `${API_BASE_URL}/Account/token/refresh/`,
        { refresh },
      )
      const newAccess = res.data.access
      if (newAccess) {
        setAuthTokens(newAccess, refresh)
      }
      return newAccess ?? null
    } catch {
      clearAuthTokens()
      return null
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const { response, config } = error
    const originalRequest = config as RetryConfig
    if (response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true
      const newAccess = await refreshAccessToken()
      if (newAccess) {
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${newAccess}`,
        }
        return http(originalRequest)
      }
    }
    return Promise.reject(error)
  },
)

export const authApi = {
  async login(payload: Pick<TokenObtainPair, 'username' | 'password'>) {
    const res = await http.post<TokenObtainPair>('/Account/login/', payload)
    return res.data
  },
  async register(payload: UserCreate) {
    const res = await http.post<UserCreate>('/Account/register/', payload)
    return res.data
  },
}

export const profileApi = {
  async homes() {
    const res = await http.get<HomeView[]>('/Profile/home/')
    return res.data
  },
  async createHome(payload: HomePost) {
    const res = await http.post<HomePost>('/Profile/home/', payload)
    return res.data
  },
  async rooms() {
    const res = await http.get<RoomView[]>('/Profile/room/')
    return res.data
  },
  async createRoom(payload: RoomPost) {
    const res = await http.post<RoomPost>('/Profile/room/', payload)
    return res.data
  },
  async lamps() {
    const res = await http.get<LampView[]>('/Profile/lamp/')
    return res.data
  },
  async createLamp(payload: LampPost) {
    const res = await http.post<LampPost>('/Profile/lamp/', payload)
    return res.data
  },
  async setLampStatus(id: number, payload: LampStatusUpdate) {
    const res = await http.patch<LampView>(`/Profile/lamp/${id}/status/`, payload)
    return res.data
  },
}

export const voiceApi = {
  async sendCommand(audio: File) {
    const form = new FormData()
    form.append('audio', audio)
    const res = await http.post<VoiceCommandResult>('/api/voice/command/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },
}

export { API_BASE_URL, http }

