import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { AnimatePresence, motion } from 'framer-motion'
import { useIsFetching, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Home, DoorOpen, Lightbulb, ChevronDown } from 'lucide-react'
import { profileApi, API_BASE_URL, getAccessToken, getApiErrorMessage } from '../../api/http'
import type { HomeView, LampView, RoomView } from '../../api/types'
import { useAuth } from '../../auth/AuthProvider'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { Pill } from '../../components/ui/Pill'
import { Skeleton } from '../../components/ui/Skeleton'
import { useToast } from '../../components/ui/useToast'
import type { AxiosError } from 'axios'

type MapByKey<T> = Record<string, T[]>

const accentFromString = (value: string) => {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = value.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  const primary = `hsl(${hue}, 75%, 60%)`
  const secondary = `hsl(${(hue + 25) % 360}, 70%, 50%)`
  return {
    gradient: `linear-gradient(135deg, ${primary}, ${secondary})`,
    border: `1px solid hsla(${hue}, 65%, 45%, 0.3)`,
    hue,
  }
}

const EmptyState = ({ title, body }: { title: string; body: string }) => (
  <Card className="flex flex-col items-center gap-2 text-center text-slate-600">
    <div className="h-10 w-10 rounded-full bg-slate-100 text-lg font-bold text-slate-500">◎</div>
    <div>
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      <p className="text-sm text-slate-600">{body}</p>
    </div>
  </Card>
)

const TokenCopy = ({ token }: { token?: string }) => {
  const [copied, setCopied] = useState(false)
  if (!token) return null

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(token)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return (
    <Button variant="ghost" size="sm" onClick={copy}>
      {copied ? 'Copied' : 'Copy token'}
    </Button>
  )
}

type AddHomeInputs = { name: string }
type AddRoomInputs = { name: string }
type AddLampInputs = { name: string; status?: boolean }

const homeSchema = z.object({ name: z.string().min(1, 'Name is required') })
const roomSchema = z.object({ name: z.string().min(1, 'Name is required') })
const lampSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  status: z.boolean().optional(),
})

const LampRow = ({
  lamp,
  onToggle,
  loading,
}: {
  lamp: LampView
  onToggle: (lamp: LampView) => void
  loading?: boolean
}) => (
  <div className="flex flex-col gap-2 rounded-lg border border-slate-100 bg-white/60 p-3">
    <div className="flex items-start justify-between gap-3">
      <div>
        <p className="text-sm font-semibold text-slate-900">{lamp.name}</p>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-600">
          <Pill tone={lamp.status ? 'green' : 'slate'}>{lamp.status ? 'On' : 'Off'}</Pill>
          <Pill tone={lamp.connection ? 'green' : 'rose'}>
            {lamp.connection ? 'Connected' : 'Offline'}
          </Pill>
          {lamp.shared_with.length === 0 ? (
            <Pill tone="slate">Private</Pill>
          ) : (
            lamp.shared_with.map((user) => (
              <Pill key={user} tone="blue">
                {user}
              </Pill>
            ))
          )}
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <button
          type="button"
          onClick={() => onToggle(lamp)}
          disabled={loading || !lamp.connection}
          className={`relative h-6 w-12 rounded-full transition-colors duration-200 ${
            lamp.status ? 'bg-emerald-400/80' : 'bg-slate-200'
          } ${!lamp.connection ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
        >
          <div
            className={`absolute left-1 top-1 h-4 w-4 rounded-full bg-white shadow transition-transform duration-200 ${
              lamp.status ? 'translate-x-6' : ''
            }`}
          />
        </button>
        <p className="text-[11px] text-slate-500">
          {lamp.connection ? (loading ? 'Updating…' : 'Tap to toggle') : 'Offline (cannot toggle)'}
        </p>
        <TokenCopy token={lamp.token} />
      </div>
    </div>
  </div>
)

type RoomProps = {
  room: RoomView
  lamps: LampView[]
  onAddLamp: (roomId: number) => void
  onToggleLamp: (lamp: LampView) => void
  togglingLampId?: number | null
}

const RoomBlock = ({ room, lamps, onAddLamp, onToggleLamp, togglingLampId }: RoomProps) => (
  <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
    <div className="mb-2 flex items-center justify-between">
      <div>
        <p className="text-sm font-semibold text-slate-900">{room.name}</p>
        <p className="text-xs text-slate-600">{lamps.length} lamp(s)</p>
      </div>
      <Button variant="ghost" size="sm" onClick={() => onAddLamp(room.id)}>
        <Lightbulb className="h-3.5 w-3.5" />
        Add lamp
      </Button>
    </div>
    <div className="space-y-2">
      {lamps.length === 0 ? (
        <p className="text-xs text-slate-500">No lamps yet.</p>
      ) : (
        lamps.map((lamp) => (
          <LampRow
            key={lamp.id}
            lamp={lamp}
            onToggle={onToggleLamp}
            loading={togglingLampId === lamp.id}
          />
        ))
      )}
    </div>
  </div>
)

type HomeCardProps = {
  home: HomeView
  rooms: RoomView[]
  lampsByRoom: Record<number, LampView[]>
  expanded: boolean
  onToggle: (id: number) => void
  onAddRoom: (homeId: number) => void
  onAddLamp: (roomId: number) => void
  onToggleLamp: (lamp: LampView) => void
  togglingLampId?: number | null
}

const HomeCard = ({
  home,
  rooms,
  lampsByRoom,
  expanded,
  onToggle,
  onAddRoom,
  onAddLamp,
  onToggleLamp,
  togglingLampId,
}: HomeCardProps) => {
  const accent = accentFromString(home.name)
  const lampCount = rooms.reduce((count, room) => count + (lampsByRoom[room.id]?.length ?? 0), 0)

  return (
    <motion.div
      layout
      transition={{ type: 'spring', stiffness: 120, damping: 16 }}
      className="h-fit overflow-hidden rounded-2xl bg-white/80 shadow-card"
      style={{ border: accent.border }}
    >
      <div
        className="p-4 text-white"
        style={{
          backgroundImage: accent.gradient,
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-white/80">Home</p>
            <h3 className="text-xl font-semibold">{home.name}</h3>
            <p className="text-sm text-white/80">Owner: {home.owner_username}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Pill tone="slate">Shared: {home.shared_with.length}</Pill>
            <Pill tone="orange">Rooms: {rooms.length}</Pill>
            <Pill tone="green">Lamps: {lampCount}</Pill>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm text-white/90">
            Expand to manage rooms and lamps. Changes refresh automatically.
          </p>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" onClick={() => onAddRoom(home.id)}>
              <DoorOpen className="h-3.5 w-3.5" />
              Add room
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onToggle(home.id)}
              className="bg-white/20 text-white border-white/30 hover:bg-white/30 hover:border-white/40 shadow-sm"
            >
              <span className="text-xs font-semibold">{expanded ? 'Collapse' : 'Expand'}</span>
              <motion.div
                animate={{ rotate: expanded ? 180 : 0 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <ChevronDown className="h-3.5 w-3.5" />
              </motion.div>
            </Button>
          </div>
        </div>
      </div>
      <AnimatePresence initial={false} mode="sync">
        {expanded && (
          <motion.div
            className="space-y-3 p-4"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
          >
            {rooms.length === 0 ? (
              <EmptyState title="No rooms yet" body="Add your first room to organize lamps." />
            ) : (
              rooms.map((room) => (
                <RoomBlock
                  key={room.id}
                  room={room}
                  lamps={lampsByRoom[room.id] ?? []}
                  onAddLamp={onAddLamp}
                  onToggleLamp={onToggleLamp}
                  togglingLampId={togglingLampId}
                />
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

const useGrouping = (
  rooms?: RoomView[],
  lamps?: LampView[],
): { roomsByHome: Record<number, RoomView[]>; lampsByRoom: Record<number, LampView[]> } => {
  const roomsByHome = useMemo<Record<number, RoomView[]>>(() => {
    const acc: Record<number, RoomView[]> = {}
    rooms?.forEach((room) => {
      const key = room.home_id
      acc[key] = acc[key] ? [...acc[key], room] : [room]
    })
    return acc
  }, [rooms])

  const lampsByRoom = useMemo<Record<number, LampView[]>>(() => {
    const acc: Record<number, LampView[]> = {}
    lamps?.forEach((lamp) => {
      const key = lamp.room_id
      acc[key] = acc[key] ? [...acc[key], lamp] : [lamp]
    })
    return acc
  }, [lamps])

  return { roomsByHome, lampsByRoom }
}

const ModalHome = ({
  open,
  onClose,
  onSubmit,
  loading,
}: {
  open: boolean
  onClose: () => void
  onSubmit: (data: AddHomeInputs) => Promise<void>
  loading: boolean
}) => {
  const form = useForm<AddHomeInputs>({
    resolver: zodResolver(homeSchema),
    defaultValues: { name: '' },
  })

  const handleSubmit = form.handleSubmit(async (data) => {
    await onSubmit(data)
    form.reset()
  })

  return (
    <Modal open={open} onClose={onClose} title="Add home">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input label="Name" placeholder="Beach house" {...form.register('name')} error={form.formState.errors.name?.message} />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Save home
          </Button>
        </div>
      </form>
    </Modal>
  )
}

const ModalRoom = ({
  open,
  onClose,
  onSubmit,
  loading,
  homeName,
}: {
  open: boolean
  homeName?: string
  onClose: () => void
  onSubmit: (data: AddRoomInputs) => Promise<void>
  loading: boolean
}) => {
  const form = useForm<AddRoomInputs>({
    resolver: zodResolver(roomSchema),
    defaultValues: { name: '' },
  })

  const handleSubmit = form.handleSubmit(async (data) => {
    await onSubmit(data)
    form.reset()
  })

  return (
    <Modal open={open} onClose={onClose} title="Add room" description={homeName ? `Home: ${homeName}` : undefined}>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input label="Name" placeholder="Living room" {...form.register('name')} error={form.formState.errors.name?.message} />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Save room
          </Button>
        </div>
      </form>
    </Modal>
  )
}

const ModalLamp = ({
  open,
  onClose,
  onSubmit,
  loading,
  roomName,
}: {
  open: boolean
  roomName?: string
  onClose: () => void
  onSubmit: (data: AddLampInputs) => Promise<void>
  loading: boolean
}) => {
  const form = useForm<AddLampInputs>({
    resolver: zodResolver(lampSchema),
    defaultValues: { name: '', status: false },
  })

  const handleSubmit = form.handleSubmit(async (data) => {
    await onSubmit(data)
    form.reset({ name: '', status: false })
  })

  return (
    <Modal open={open} onClose={onClose} title="Add lamp" description={roomName ? `Room: ${roomName}` : undefined}>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input label="Name" placeholder="Floor lamp" {...form.register('name')} error={form.formState.errors.name?.message} />
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" className="h-4 w-4 accent-slate-900" {...form.register('status')} />
          Set initial status to on
        </label>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Save lamp
          </Button>
        </div>
      </form>
    </Modal>
  )
}

const ErrorBanner = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
  <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
    <span>{message}</span>
    <Button size="sm" variant="secondary" onClick={onRetry}>
      Retry
    </Button>
  </div>
)

const HeaderBar = ({
  onAddHome,
  onLogout,
  isBusy,
}: {
  onAddHome: () => void
  onLogout: () => void
  isBusy: boolean
}) => {
  const online = navigator.onLine
  return (
    <div className="sticky top-0 z-20 mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-card backdrop-blur">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">SmartLight</p>
        <h1 className="text-2xl font-semibold text-slate-900">SmartLight Dashboard</h1>
        <p className="text-sm text-slate-600">Manage homes, rooms, and lamps in one place.</p>
      </div>
      <div className="flex items-center gap-2">
        <Pill tone={online ? 'green' : 'rose'}>{online ? 'Online' : 'Offline'}</Pill>
        <Pill tone={isBusy ? 'orange' : 'slate'}>{isBusy ? 'Syncing…' : 'Idle'}</Pill>
        <Pill tone="blue">Base: {API_BASE_URL}</Pill>
        <Button variant="secondary" onClick={onAddHome}>
          <Home className="h-4 w-4" />
          Add home
        </Button>
        <Button variant="ghost" onClick={onLogout}>
          Logout
        </Button>
      </div>
    </div>
  )
}

export const DashboardPage = () => {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isFetching = useIsFetching()
  const toast = useToast()

  const homesQuery = useQuery({ queryKey: ['homes'], queryFn: profileApi.homes })
  const roomsQuery = useQuery({ queryKey: ['rooms'], queryFn: profileApi.rooms })
  const lampsQuery = useQuery({ queryKey: ['lamps'], queryFn: profileApi.lamps })

  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [homeModal, setHomeModal] = useState(false)
  const [roomTarget, setRoomTarget] = useState<{ homeId: number; homeName: string } | null>(null)
  const [lampTarget, setLampTarget] = useState<{ roomId: number; roomName: string } | null>(null)
  const [togglingLampId, setTogglingLampId] = useState<number | null>(null)

  const { roomsByHome, lampsByRoom } = useGrouping(roomsQuery.data, lampsQuery.data)

  // --- WebSocket: live lamp status updates ---
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Build WebSocket URL from API base so we always hit Django, not the Vite dev server.
    let wsUrl: string
    try {
      const api = new URL(API_BASE_URL)
      const protocol = api.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${api.host}/ws/light/`
    } catch {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}://${window.location.hostname}:8000/ws/light/`
    }

    const accessToken = getAccessToken()
    const wsWithAuth = accessToken
      ? `${wsUrl}?token=${encodeURIComponent(accessToken)}`
      : wsUrl

    let socket: WebSocket | null = null
    let isUnmounted = false

    const connect = () => {
      if (isUnmounted) return

      socket = new WebSocket(wsWithAuth)

      socket.onopen = () => {
        // connection established
      }

      socket.onclose = () => {
        // simple auto‑reconnect with small delay
        if (!isUnmounted) {
          setTimeout(connect, 3000)
        }
      }

      socket.onerror = () => {
        // errors are logged in backend; no-op here
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as {
            token?: string
            status?: boolean
            establish?: boolean
          }

          if (!data?.token) return

          queryClient.setQueryData<LampView[]>(['lamps'], (prev) => {
            if (!prev) return prev
            return prev.map((lamp) =>
              lamp.token === data.token
                ? {
                    ...lamp,
                    status: typeof data.status === 'boolean' ? data.status : lamp.status,
                    connection:
                      typeof data.establish === 'boolean' ? data.establish : lamp.connection,
                  }
                : lamp,
            )
          })
        } catch {
          // ignore malformed payloads
        }
      }
    }

    connect()

    return () => {
      isUnmounted = true
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [queryClient])

  const createHome = useMutation({
    mutationFn: profileApi.createHome,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homes'] })
    },
  })

  const createRoom = useMutation({
    mutationFn: profileApi.createRoom,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
    },
  })

  const createLamp = useMutation({
    mutationFn: profileApi.createLamp,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lamps'] })
    },
  })

  const setLampStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: boolean }) =>
      profileApi.setLampStatus(id, { status }),
    onMutate: async ({ id, status }) => {
      setTogglingLampId(id)

      // Optimistic update: flip status in cache immediately
      await queryClient.cancelQueries({ queryKey: ['lamps'] })
      const previousLamps = queryClient.getQueryData<LampView[]>(['lamps'])

      queryClient.setQueryData<LampView[]>(['lamps'], (prev) =>
        prev?.map((lamp) => (lamp.id === id ? { ...lamp, status } : lamp)),
      )

      return { previousLamps }
    },
    onError: (error, variables, context) => {
      // Roll back optimistic update
      if (context?.previousLamps) {
        queryClient.setQueryData(['lamps'], context.previousLamps)
      }

      // Parse error and show specific toast message
      const axiosError = error as AxiosError<{ detail?: string }>
      const status = axiosError.response?.status
      const lamp = lampsQuery.data?.find((l) => l.id === variables.id)
      const lampName = lamp?.name || 'Lamp'

      let errorMessage: string

      if (status === 504) {
        // Gateway Timeout - device didn't respond
        errorMessage = `${lampName} didn't respond. The device may be offline or slow to respond. Please try again.`
      } else if (status === 403) {
        // Forbidden - no permission
        errorMessage = `You don't have permission to control ${lampName}.`
      } else if (status === 404) {
        // Not Found
        errorMessage = `${lampName} not found. It may have been deleted.`
      } else if (status === 400) {
        // Bad Request
        const detail = axiosError.response?.data?.detail || 'Invalid request'
        errorMessage = `${lampName}: ${detail}`
      } else if (!navigator.onLine || axiosError.code === 'ERR_NETWORK') {
        // Network error
        errorMessage = `Connection failed. Check your internet and try again.`
      } else if (status === 401) {
        // Unauthorized - token expired (should be handled by interceptor, but just in case)
        errorMessage = `Session expired. Please log in again.`
      } else {
        // Generic error
        const detail = axiosError.response?.data?.detail || axiosError.message || 'Unknown error'
        errorMessage = `Failed to toggle ${lampName}: ${detail}`
      }

      // Show toast notification
      toast.error(errorMessage, 7000) // Show for 7 seconds for important errors
    },
    onSuccess: (data) => {
      // Sync cache with authoritative response
      queryClient.setQueryData<LampView[]>(['lamps'], (prev) =>
        prev?.map((lamp) => (lamp.id === data.id ? data : lamp)),
      )

      // Show success toast (brief, since WebSocket will also confirm)
      const lampName = data.name || 'Lamp'
      const statusText = data.status ? 'ON' : 'OFF'
      toast.success(`${lampName} turned ${statusText}`, 3000)
    },
    onSettled: () => {
      setTogglingLampId(null)
      // Light refetch to reconcile with device/MQTT confirmation if needed
      queryClient.invalidateQueries({ queryKey: ['lamps'], refetchType: 'none' })
    },
  })

  const handleLogout = () => {
    logout()
    queryClient.clear()
    navigate('/login')
  }

  const handleAddRoom = (homeId: number) => {
    const home = homesQuery.data?.find((h) => h.id === homeId)
    setRoomTarget({ homeId, homeName: home?.name ?? '' })
  }

  const handleAddLamp = (roomId: number) => {
    const room = roomsQuery.data?.find((r) => r.id === roomId)
    setLampTarget({ roomId, roomName: room?.name ?? '' })
  }

  const submitHome = async (data: AddHomeInputs) => {
    try {
      await createHome.mutateAsync({ name: data.name })
      setHomeModal(false)
      toast.success('Home created successfully')
    } catch (error) {
      const message = getApiErrorMessage(
        error,
        'Failed to create home. Please check the name and try again.',
      )
      toast.error(message, 7000)
    }
  }

  const submitRoom = async (data: AddRoomInputs) => {
    if (!roomTarget) return
    try {
      await createRoom.mutateAsync({ name: data.name, home: roomTarget.homeId })
      setRoomTarget(null)
      toast.success('Room created successfully')
    } catch (error) {
      const message = getApiErrorMessage(
        error,
        'Failed to create room. Make sure name is unique within this home.',
      )
      toast.error(message, 7000)
    }
  }

  const submitLamp = async (data: AddLampInputs) => {
    if (!lampTarget) return
    try {
      await createLamp.mutateAsync({
        name: data.name,
        room: lampTarget.roomId,
        status: data.status,
      })
      setLampTarget(null)
      toast.success('Lamp created successfully')
    } catch (error) {
      const message = getApiErrorMessage(
        error,
        'Failed to create lamp. Please review the inputs and try again.',
      )
      toast.error(message, 7000)
    }
  }

  const handleToggleLamp = (lamp: LampView) => {
    if (!lamp.connection || setLampStatus.isPending) return
    setLampStatus.mutate({ id: lamp.id, status: !lamp.status })
  }

  const isLoading = homesQuery.isLoading || roomsQuery.isLoading || lampsQuery.isLoading
  const hasError = homesQuery.isError || roomsQuery.isError || lampsQuery.isError

  const errorMessage =
    (homesQuery.error as Error | undefined)?.message ||
    (roomsQuery.error as Error | undefined)?.message ||
    (lampsQuery.error as Error | undefined)?.message

  return (
    <div className="app-shell">
      <div className="mx-auto max-w-6xl px-4 py-6 pb-28">
        <HeaderBar onAddHome={() => setHomeModal(true)} onLogout={handleLogout} isBusy={isFetching > 0} />

        {hasError && (
          <ErrorBanner
            message={errorMessage ?? 'Something went wrong while loading data.'}
            onRetry={() => {
              homesQuery.refetch()
              roomsQuery.refetch()
              lampsQuery.refetch()
            }}
          />
        )}

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {[1, 2].map((item) => (
              <Card key={item} className="space-y-3">
                <Skeleton className="h-6 w-1/2" />
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-24 w-full" />
              </Card>
            ))}
          </div>
        ) : homesQuery.data && homesQuery.data.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:items-start md:content-start">
            {homesQuery.data.map((home) => (
              <div key={home.id} className="self-start">
                <HomeCard
                  home={home}
                  rooms={roomsByHome[home.id] ?? []}
                  lampsByRoom={lampsByRoom}
                  expanded={Boolean(expanded[home.id])}
                  onToggle={(id) => setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))}
                  onAddRoom={handleAddRoom}
                  onAddLamp={handleAddLamp}
                  onToggleLamp={handleToggleLamp}
                  togglingLampId={togglingLampId}
                />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No homes yet" body="Create your first home to get started." />
        )}
      </div>

      <ModalHome open={homeModal} onClose={() => setHomeModal(false)} onSubmit={submitHome} loading={createHome.isPending} />
      <ModalRoom
        open={Boolean(roomTarget)}
        onClose={() => setRoomTarget(null)}
        onSubmit={submitRoom}
        loading={createRoom.isPending}
        homeName={roomTarget?.homeName}
      />
      <ModalLamp
        open={Boolean(lampTarget)}
        onClose={() => setLampTarget(null)}
        onSubmit={submitLamp}
        loading={createLamp.isPending}
        roomName={lampTarget?.roomName}
      />
    </div>
  )
}

