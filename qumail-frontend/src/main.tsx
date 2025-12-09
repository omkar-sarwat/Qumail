// React import not needed with new JSX transform
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import './index.css'

// CRITICAL: Handle OAuth callback redirect BEFORE React mounts
// Google OAuth returns to /auth/callback but we use HashRouter (/#/auth/callback)
// This must run synchronously before React renders
(function handleOAuthRedirect() {
  const path = window.location.pathname
  const search = window.location.search
  
  // If we're at /auth/callback with OAuth params, redirect to hash route
  if (path === '/auth/callback' && search) {
    console.log('🔄 OAuth callback detected, redirecting to hash route...')
    // Redirect to /#/auth/callback with the same query params
    window.location.replace(`${window.location.origin}/#/auth/callback${search}`)
    return // Stop execution, page will reload
  }
})()

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 401 (unauthorized) errors
        if (error?.response?.status === 401) return false
        return failureCount < 3
      },
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
)