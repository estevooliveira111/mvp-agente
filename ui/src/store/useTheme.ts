import { create } from 'zustand'

type Theme = 'dark' | 'light' | 'system'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
}

export const useTheme = create<ThemeState>((set) => ({
  theme: (localStorage.getItem('ui-theme') as Theme) || 'system',
  setTheme: (theme) => {
    localStorage.setItem('ui-theme', theme)
    set({ theme })
  },
}))
