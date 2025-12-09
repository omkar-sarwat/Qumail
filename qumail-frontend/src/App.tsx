import React, { useState, Suspense, lazy } from 'react'
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { LoginScreen } from './components/auth/LoginScreen'
import { OAuthCallback } from './components/auth/OAuthCallback'
import { MicrosoftOAuthCallback } from './components/auth/MicrosoftOAuthCallback'
import { YahooOAuthCallback } from './components/auth/YahooOAuthCallback'
import { AuthProvider, useAuth } from './context/AuthContext'
import { EmailSyncProvider } from './services/EmailSyncProvider'
import { TitleBar } from './components/TitleBar'
import SplashScreen from './components/SplashScreen'
import ErrorBoundary from './components/ErrorBoundary'
import OfflineIndicator from './components/OfflineIndicator'

// Lazy load heavy components for better initial load
const MainDashboard = lazy(() => import('./components/dashboard/MainDashboard').then(m => ({ default: m.MainDashboard })))

// Loading fallback for lazy components
const LazyLoadFallback: React.FC = () => (
  <div className="min-h-full bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="text-gray-500 text-sm">Loading...</p>
    </div>
  </div>
)

// Inner component that uses auth context
const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()
  const [showSplash, setShowSplash] = useState(true)

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-white">
      {/* Offline/slow connection indicator */}
      <OfflineIndicator />
      
      {showSplash && <SplashScreen onFinish={() => setShowSplash(false)} />}
      
      {/* Hide content completely during splash */}
      <div className={`flex-1 flex flex-col overflow-hidden transition-opacity duration-200 ${showSplash ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
        {window.electronAPI && <TitleBar />}
        <div className="flex-1 overflow-hidden flex flex-col">
          {isLoading && !showSplash ? (
            <div className="min-h-full bg-gray-50 flex items-center justify-center">
              <div className="text-center">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Initializing QuMail
                </h2>
                <p className="text-gray-500">
                  Checking quantum security status...
                </p>
              </div>
            </div>
          ) : (
          <Suspense fallback={<LazyLoadFallback />}>
            <Routes>
              <Route
                path="/auth/callback"
                element={<OAuthCallback onAuthComplete={() => {
                  // OAuthCallback component will use the auth context directly
                  // No need to handle it here
                }} />}
              />
              <Route
                path="/auth/microsoft/callback"
                element={<MicrosoftOAuthCallback />}
              />
              <Route
                path="/auth/yahoo/callback"
                element={<YahooOAuthCallback />}
              />
              <Route
                path="/dashboard"
                element={
                  isAuthenticated ? (
                    <MainDashboard />
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />
              <Route
                path="/"
                element={
                  isAuthenticated ? (
                    <Navigate to="/dashboard" replace />
                  ) : (
                    <LoginScreen />
                  )
                }
              />
              <Route
                path="*"
                element={<Navigate to="/" replace />}
              />
            </Routes>
          </Suspense>
        )}

        </div>
      </div>

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            borderRadius: '12px',
            fontSize: '14px',
            fontWeight: '500',
            padding: '12px 16px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </div>
  )
}

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <EmailSyncProvider>
            <AppContent />
          </EmailSyncProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  )
}

export default App