import { create } from 'zustand'

interface AuthState {
  isAuthenticated: boolean
  user: any | null
  token: string | null
  login: (token: string, user: any) => void
  logout: () => void
}

export const useAuth = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('token'),
  user: null,
  token: localStorage.getItem('token'),
  login: (token, user) => {
    localStorage.setItem('token', token)
    set({ isAuthenticated: true, user, token })
  },
  logout: () => {
    localStorage.removeItem('token')
    set({ isAuthenticated: false, user: null, token: null })
  },
}))
