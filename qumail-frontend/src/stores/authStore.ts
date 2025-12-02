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
  _hasHydrated: boolean

  // Actions
  setAuthData: (user: User, token: string) => void
  setLoginUrl: (url: string) => void
  login: () => Promise<boolean>
  logout: () => void
  clearError: () => void
  checkAuthStatus: () => Promise<void>
  getGoogleAuthUrl: () => Promise<string | null>
  handleOAuthCallback: (code: string, state: string) => Promise<boolean>
  setHasHydrated: (state: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state - will be overwritten by persisted data
      isAuthenticated: false,
      isLoading: true,
      user: null,
      sessionToken: null,
      loginUrl: null,
      error: null,
      _hasHydrated: false,

      // Mark that store has been hydrated from storage
      setHasHydrated: (state: boolean) => {
        set({ _hasHydrated: state })
      },

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
        
        // Also store in legacy localStorage key for MainDashboard compatibility
        localStorage.setItem('authToken', token)
        localStorage.setItem('user', JSON.stringify(user))
        
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
        
        // Clear legacy localStorage keys
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        
        toast.success('Logged out successfully')
      },

      // Clear error
      clearError: () => {
        set({ error: null })
      },

      // Check authentication status
      checkAuthStatus: async () => {
        const { sessionToken, user } = get()
        
        // If we have token and user, immediately set authenticated
        if (sessionToken && user) {
          console.log('📴 [AuthStore] Has stored credentials - setting authenticated')
          set({
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          apiService.setAuthToken(sessionToken)
          
          // If offline, we're done
          if (!navigator.onLine) {
            console.log('📴 [AuthStore] Offline mode - using cached auth')
            return
          }
          
          // If online, verify in background (don't block UI)
          console.log('🌐 [AuthStore] Online - verifying auth in background')
          try {
            const response = await apiService.validateAuth()
            if (!response.isAuthenticated) {
              console.log('⚠️ [AuthStore] Server says not authenticated - clearing')
              set({
                isAuthenticated: false,
                user: null,
                sessionToken: null,
                isLoading: false,
              })
              apiService.clearAuthToken()
            } else {
              console.log('✅ [AuthStore] Server verified authentication')
            }
          } catch (error: any) {
            // Network error - keep cached auth
            console.log('⚠️ [AuthStore] Verification failed - keeping cached auth:', error.message)
          }
          return
        }
        
        // No stored credentials
        console.log('❌ [AuthStore] No stored credentials')
        set({ isLoading: false, isAuthenticated: false })
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
          
          // OPTIMIZATION: Prefetch emails in background immediately after login
          // This makes the inbox load instantly when user navigates to it
          setTimeout(() => {
            console.log('⚡ Prefetching emails in background after login...');
            import('./emailStore').then(({ useEmailStore }) => {
              useEmailStore.getState().fetchEmails({ folder: 'gmail_inbox' as any }, true);
            });
          }, 100);
          
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
        isAuthenticated: state.isAuthenticated, // Also persist this!
      }),
      onRehydrateStorage: () => (state) => {
        // Called when store is rehydrated from localStorage
        if (state) {
          console.log('🔄 [AuthStore] Rehydrated from storage')
          console.log('🔄 [AuthStore] Has user:', !!state.user)
          console.log('🔄 [AuthStore] Has token:', !!state.sessionToken)
          
          // If we have user and token, set authenticated immediately
          if (state.user && state.sessionToken) {
            state.isAuthenticated = true
            state.isLoading = false
            apiService.setAuthToken(state.sessionToken)
            
            // IMPORTANT: Also sync to legacy localStorage keys for MainDashboard
            localStorage.setItem('authToken', state.sessionToken)
            localStorage.setItem('user', JSON.stringify(state.user))
            
            console.log('✅ [AuthStore] Auto-authenticated from storage (synced to authToken)')
          } else {
            state.isLoading = false
          }
          
          state._hasHydrated = true
        }
      },
    }
  )
)