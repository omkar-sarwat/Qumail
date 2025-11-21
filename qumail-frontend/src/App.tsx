import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { LoginScreen } from './components/auth/LoginScreen'
import { OAuthCallback } from './components/auth/OAuthCallback'
import { MainDashboard } from './components/dashboard/MainDashboard'
import { AuthProvider, useAuth } from './context/AuthContext'
import { TitleBar } from './components/TitleBar'

// Inner component that uses auth context
const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-4 mx-auto">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </motion.div>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Initializing QuMail
          </h2>
          <p className="text-gray-300">
            Checking quantum security status...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden flex flex-col">
      {window.electronAPI && <TitleBar />}
      <div className="flex-1 overflow-hidden flex flex-col">
        <Routes>
        <Route 
          path="/auth/callback" 
          element={<OAuthCallback onAuthComplete={() => {
            // OAuthCallback component will use the auth context directly
            // No need to handle it here
          }} />} 
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
    </div>
  )
}

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  )
}

export default App