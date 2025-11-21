import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import toast from 'react-hot-toast'
import { apiService } from '../services/api'

interface User {
  email: string
  displayName: string
  lastLogin?: string
  createdAt: string
  oauthConnected: boolean
  tokenExpiresAt?: string
}

interface AuthState {
  // State
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  sessionToken: string | null
  loginUrl: string | null
  error: string | null

  // Actions
  setAuthData: (user: User, token: string) => void
  setLoginUrl: (url: string) => void
  login: () => Promise<boolean>
  logout: () => void
  clearError: () => void
  checkAuthStatus: () => Promise<void>
  getGoogleAuthUrl: () => Promise<string | null>
  handleOAuthCallback: (code: string, state: string) => Promise<boolean>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      isLoading: true,
      user: null,
      sessionToken: null,
      loginUrl: null,
      error: null,

      // Set authentication data
      setAuthData: (user: User, token: string) => {
        set({
          isAuthenticated: true,
          user,
          sessionToken: token,
          error: null,
          isLoading: false,
        })
        
        // Set token in API service
        apiService.setAuthToken(token)
        
        toast.success(`Welcome back, ${user.displayName || user.email}!`)
      },

      // Set login URL
      setLoginUrl: (url: string) => {
        set({ loginUrl: url })
      },

      // Login function - OAuth flow
      login: async () => {
        try {
          set({ isLoading: true, error: null })
          
          // Get Google OAuth URL
          const authUrl = await get().getGoogleAuthUrl()
          if (!authUrl) {
            throw new Error('Failed to get authentication URL')
          }
          
          // Open OAuth URL in browser
          if (window.electronAPI) {
            await window.electronAPI.openExternal(authUrl)
            // In Electron, the callback will be handled in a new window
            // We'll wait for the auth process to complete
            toast.success('Please complete authentication in your browser')
          } else {
            // In web browser, navigate to OAuth URL
            window.location.href = authUrl
          }
          
          set({ isLoading: false })
          return true
        } catch (error: any) {
          console.error('Login failed:', error)
          set({ 
            error: error.message || 'Login failed', 
            isLoading: false 
          })
          return false
        }
      },

      // Logout user
      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          sessionToken: null,
          loginUrl: null,
          error: null,
          isLoading: false,
        })
        
        // Clear token from API service
        apiService.clearAuthToken()
        
        toast.success('Logged out successfully')
      },

      // Clear error
      clearError: () => {
        set({ error: null })
      },

      // Check authentication status
      checkAuthStatus: async () => {
        const { sessionToken } = get()
        
        if (!sessionToken) {
          set({ isLoading: false, isAuthenticated: false })
          return
        }

        try {
          set({ isLoading: true })
          
          // Set token in API service
          apiService.setAuthToken(sessionToken)
          
          // Validate token with backend
          const response = await apiService.validateAuth()
          
          if (response.isAuthenticated) {
            set({
              isAuthenticated: true,
              user: {
                email: response.email,
                // response.name may be undefined; fallback to email prefix
                displayName: response.name || response.email?.split('@')[0] || response.email,
                lastLogin: new Date().toISOString(),
                createdAt: new Date().toISOString(),
                oauthConnected: true,
              },
              isLoading: false,
              error: null,
            })
          } else {
            // Token is invalid, clear auth
            set({
              isAuthenticated: false,
              user: null,
              sessionToken: null,
              isLoading: false,
            })
            apiService.clearAuthToken()
          }
        } catch (error) {
          console.error('Auth check failed:', error)
          set({
            isAuthenticated: false,
            user: null,
            sessionToken: null,
            isLoading: false,
            error: 'Authentication check failed',
          })
          apiService.clearAuthToken()
        }
      },

      // Get Google OAuth URL
      getGoogleAuthUrl: async () => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await apiService.getGoogleAuthUrl()
          
          set({
            loginUrl: response.auth_url,
            isLoading: false,
          })
          
          return response.auth_url
        } catch (error: any) {
          console.error('Failed to get auth URL:', error)
          const errorMessage = error.response?.data?.detail || 'Failed to get authorization URL'
          
          set({
            error: errorMessage,
            isLoading: false,
          })
          
          toast.error(errorMessage)
          return null
        }
      },

      // Handle OAuth callback
      handleOAuthCallback: async (code: string, state: string) => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await apiService.handleOAuthCallback(code, state)
          
          const user: User = {
            email: response.user_email,
            displayName: response.user_email.split('@')[0], // Use email prefix as display name
            createdAt: new Date().toISOString(),
            oauthConnected: true,
            tokenExpiresAt: response.expires_at,
          }
          
          get().setAuthData(user, response.session_token)
          return true
        } catch (error: any) {
          console.error('OAuth callback failed:', error)
          const errorMessage = error.response?.data?.detail || 'OAuth authentication failed'
          
          set({
            error: errorMessage,
            isLoading: false,
          })
          
          toast.error(errorMessage)
          return false
        }
      },
    }),
    {
      name: 'qumail-auth',
      partialize: (state) => ({
        sessionToken: state.sessionToken,
        user: state.user,
      }),
    }
  )
)