import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Card, CardContent } from '../ui/Card'
import { authService } from '../../services/authService'
import { useAuth } from '../../context/AuthContext'
import { toast } from 'react-hot-toast'

// Global flag to prevent multiple OAuth processing
let isOAuthProcessing = false

interface OAuthCallbackProps {
  onAuthComplete: (success: boolean) => void
}

export const OAuthCallback: React.FC<OAuthCallbackProps> = ({ onAuthComplete }) => {
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Authenticating with Google...')
  const [hasProcessed, setHasProcessed] = useState(false) // Prevent multiple calls
  const navigate = useNavigate()
  const [, setError] = useState<string | null>(null)
  const { refreshUser } = useAuth()

  useEffect(() => {
    // If running in Electron, OAuth is handled by IPC in LoginScreen, skip this component
    const isElectron = !!(window as any).electronAPI
    if (isElectron) {
      console.log('Running in Electron - OAuth handled by IPC, skipping callback component')
      navigate('/', { replace: true })
      return
    }
    
    // Check global processing flag first
    if (isOAuthProcessing) {
      console.log('OAuth already processing globally, skipping')
      return
    }
    
    // Check if we've already processed this callback
    if (hasProcessed) {
      console.log('OAuth callback already processed, skipping')
      return
    }
    
    // Extract URL parameters ONCE and clear them immediately
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const state = urlParams.get('state')
    const error = urlParams.get('error')
    
    // Clear URL parameters IMMEDIATELY to prevent reuse
    window.history.replaceState({}, document.title, window.location.pathname)
    
    if (!code && !error) {
      console.log('No OAuth parameters found, ignoring')
      return
    }
    
    const handleCallback = async () => {
      // Set global and local flags
      isOAuthProcessing = true
      setHasProcessed(true)
      
      try {
        console.log('OAuth callback params:', { 
          code: code ? code.substring(0, 10) + '...' : null, 
          state, 
          error,
          timestamp: new Date().toISOString()
        })

        if (error) {
          setStatus('error')
          setMessage(`Authentication failed: ${error}`)
          setError(error)
          toast.error(`Authentication failed: ${error}`)
          setTimeout(() => onAuthComplete(false), 3000)
          return
        }

        if (!code) {
          throw new Error('No authorization code received from Google')
        }

        // Verify state matches what we stored to prevent CSRF
        const storedState = localStorage.getItem('oauth_state')
        if (!state || state !== storedState) {
          throw new Error('Invalid OAuth state - possible CSRF attack')
        }

        console.log('Sending callback request to backend...')
        setMessage('Exchanging authorization code for access token...')
        
        // Exchange the authorization code for tokens using authService
        const authResult = await authService.handleCallback(code, state)
        console.log('Authentication successful:', authResult.user_email)
        
        // authService has already stored tokens and user info
        setStatus('success')
        setMessage(`Welcome ${authResult.user_email}! Setting up quantum security...`)
        
        // Refresh AuthContext user state to update isAuthenticated
        await refreshUser()
        
        // Initialize quantum key pool
        try {
          const response = await fetch('http://localhost:8000/api/v1/emails/quantum/pool/initialize', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
              'Content-Type': 'application/json'
            }
          })
          
          if (!response.ok) {
            console.warn('Quantum pool initialization failed:', await response.text())
          }
        } catch (e) {
          console.warn('Failed to initialize quantum pool:', e)
        }
        
        // Show success message with quantum security status
        setMessage(`Welcome ${authResult.user_email}! Your quantum-secure mailbox is ready.`)
        
        // Complete authentication after short delay to show success message
        setTimeout(() => {
          onAuthComplete(true)
          navigate('/dashboard', { replace: true })
          toast.success('Successfully logged in with quantum security enabled')
        }, 1200)
        
      } catch (error) {
        console.error('OAuth callback error:', error)
        setStatus('error')
        const errorMessage = error instanceof Error ? error.message : 'Authentication failed'
        setMessage(errorMessage)
        setError(errorMessage)
        toast.error(errorMessage)
        
        setTimeout(() => {
          onAuthComplete(false)
          navigate('/', { replace: true })
        }, 3000)
      } finally {
        // Reset flags and clear stored state
        isOAuthProcessing = false
        localStorage.removeItem('oauth_state')
      }
    }

      // Process the callback
      handleCallback()
    }, [onAuthComplete, hasProcessed, navigate]) // Dependencies to prevent infinite loops

    // Cleanup function to reset global flag if component unmounts
    useEffect(() => {
      return () => {
        isOAuthProcessing = false
      }
    }, [])

  const spinnerVariants = {
    animate: {
      rotate: 360,
      transition: {
        duration: 1,
        repeat: Infinity,
        ease: "linear"
      }
    }
  }

  const pulseVariants = {
    animate: {
      scale: [1, 1.1, 1],
      opacity: [0.7, 1, 0.7],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return (
          <motion.div
            variants={spinnerVariants}
            animate="animate"
            className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full"
          />
        )
      case 'success':
        return (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center"
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </motion.div>
        )
      case 'error':
        return (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center"
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </motion.div>
        )
      default:
        return null
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'processing': return 'text-blue-600'
      case 'success': return 'text-green-600'
      case 'error': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Animated Orbs */}
        <motion.div 
          variants={pulseVariants}
          animate="animate"
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" 
        />
        <motion.div 
          variants={pulseVariants}
          animate="animate"
          style={{ animationDelay: '1s' }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl" 
        />
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-md mx-auto"
        >
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-2xl mb-4 mx-auto">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            
            <h1 className="text-2xl font-bold text-white mb-2">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                QuMail
              </span>
            </h1>
          </div>

          {/* Status Card */}
          <Card className="bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl">
            <CardContent className="p-8 text-center">
              <div className="mb-6 flex justify-center">
                {getStatusIcon()}
              </div>
              
              <h2 className="text-xl font-semibold text-white mb-2">
                {status === 'processing' && 'Authenticating...'}
                {status === 'success' && 'Success!'}
                {status === 'error' && 'Authentication Failed'}
              </h2>
              
              <p className={`text-sm ${getStatusColor() === 'text-blue-600' ? 'text-gray-300' : getStatusColor()}`}>
                {message}
              </p>

              {status === 'processing' && (
                <div className="mt-6">
                  <div className="flex justify-center space-x-1">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        animate={{
                          scale: [1, 1.2, 1],
                          opacity: [0.5, 1, 0.5]
                        }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          delay: i * 0.2
                        }}
                        className="w-2 h-2 bg-blue-400 rounded-full"
                      />
                    ))}
                  </div>
                </div>
              )}

              {status === 'success' && (
                <div className="mt-4 text-xs text-gray-400">
                  Quantum encryption keys synchronized
                </div>
              )}
            </CardContent>
          </Card>

          {/* Security Info */}
          <div className="mt-6 text-center text-xs text-gray-400">
            <div className="flex justify-center items-center space-x-4">
              <div className="flex items-center space-x-1">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                <span>Secure Connection</span>
              </div>
              <div className="flex items-center space-x-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Quantum Protected</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default OAuthCallback