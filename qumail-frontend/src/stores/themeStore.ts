import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  actualTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  initializeTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      actualTheme: 'light',

      setTheme: (theme: Theme) => {
        set({ theme })
        get().initializeTheme()
      },

      initializeTheme: () => {
        const { theme } = get()
        let actualTheme: 'light' | 'dark' = 'light'

        if (theme === 'system') {
          actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        } else {
          actualTheme = theme
        }

        set({ actualTheme })

        // Apply theme to document
        if (actualTheme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },
    }),
    {
      name: 'qumail-theme',
    }
  )
)

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const store = useThemeStore.getState()
    if (store.theme === 'system') {
      store.initializeTheme()
    }
  })
}