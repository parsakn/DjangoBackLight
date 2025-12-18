export interface TokenObtainPair {
  username: string
  password: string
  access?: string
  refresh?: string
}

export interface TokenRefresh {
  refresh: string
  access?: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  password2: string
  phone_number: string
}

export interface HomeView {
  id: number
  name: string
  owner_username: string
  shared_with: string[]
}

export interface HomePost {
  id?: number
  name: string
  shared_with_id?: number[]
}

export interface RoomView {
  id: number
  name: string
  home: string
  home_id: number
}

export interface RoomPost {
  id?: number
  name: string
  home: number
}

export interface LampView {
  id: number
  room: string
  room_id: number
  shared_with: string[]
  name: string
  status: boolean
  connection?: boolean
  token?: string
}

export interface LampPost {
  id?: number
  name: string
  status?: boolean
  room: number
  shared_with_id?: number[]
}

export interface LampStatusUpdate {
  status: boolean
}

export type VoiceCommandResult =
  | {
      action: 'create_home'
      home: HomeView | { id: number; name: string }
    }
  | {
      action: 'create_room'
      room: RoomView & { home_name?: string }
    }
  | {
      action: 'create_lamp'
      lamp: LampView & { home_id?: number; home_name?: string }
    }
  | {
      action: 'set_lamp_status'
      lamp: LampView & { home_id?: number; home_name?: string }
    }
  | Record<string, unknown>

