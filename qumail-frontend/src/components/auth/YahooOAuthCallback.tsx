import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Card, CardContent } from '../ui/Card'
import { toast } from 'react-hot-toast'
import apiService from '../../services/api'

// Global flag to prevent multiple OAuth processing
let isYahooOAuthProcessing = false

interface YahooOAuthCallbackProps {
  onAuthComplete?: (success: boolean) => void
}

export const YahooOAuthCallback: React.FC<YahooOAuthCallbackProps> = ({ onAuthComplete }) => {
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Authenticating with Yahoo...')
  const [hasProcessed, setHasProcessed] = useState(false)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    // Check global processing flag first
    if (isYahooOAuthProcessing) {
      console.log('Yahoo OAuth already processing globally, skipping')
      return
    }
    
    // Check if we've already processed this callback
    if (hasProcessed) {
      console.log('Yahoo OAuth callback already processed, skipping')
      return
    }
    
    // Extract URL parameters ONCE
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')
    const errorDescription = searchParams.get('error_description')
    
    // Clear URL parameters IMMEDIATELY to prevent reuse
    window.history.replaceState({}, document.title, window.location.pathname)
    
    if (!code && !error) {
      console.log('No Yahoo OAuth parameters found, ignoring')
      return
    }
    
    const handleCallback = async () => {
      // Set global and local flags
      isYahooOAuthProcessing = true
      setHasProcessed(true)
      
      try {
        console.log('Yahoo OAuth callback params:', { 
          code: code ? code.substring(0, 10) + '...' : null, 
          state, 
          error,
          timestamp: new Date().toISOString()
        })

        if (error) {
          const errorMsg = errorDescription || error
          setStatus('error')
          setMessage(`Yahoo authentication failed: ${errorMsg}`)
          toast.error(`Yahoo authentication failed: ${errorMsg}`)
          setTimeout(() => {
            onAuthComplete?.(false)
            navigate('/settings', { replace: true })
          }, 3000)
          return
        }

        if (!code) {
          throw new Error('No authorization code received from Yahoo')
        }

        // Verify state matches what we stored
        const storedState = localStorage.getItem('yahoo_oauth_state')
        if (state && storedState && state !== storedState) {
          throw new Error('Invalid OAuth state - possible CSRF attack')
        }

        console.log('Sending Yahoo callback request to backend...')
        setMessage('Exchanging authorization code for access token...')
        
        // Exchange the authorization code for tokens
        const data = await apiService.exchangeYahooCode(code, state || '')
        
        if (!data.success) {
          throw new Error(data.message || 'Yahoo OAuth failed')
        }
        
        // Clear stored state
        localStorage.removeItem('yahoo_oauth_state')
        
        console.log('Yahoo authentication successful:', data.email)
        
        setStatus('success')
        setMessage(`Yahoo account connected: ${data.email}`)
        toast.success(`Yahoo account connected: ${data.email}`)
        
        // Redirect after success
        setTimeout(() => {
          onAuthComplete?.(true)
          navigate('/dashboard', { replace: true })
        }, 2000)
        
      } catch (err: any) {
        console.error('Yahoo OAuth callback error:', err)
        setStatus('error')
        const errorMsg = err.response?.data?.detail || err.message || 'Yahoo authentication failed'
        setMessage(errorMsg)
        toast.error(errorMsg)
        
        setTimeout(() => {
          onAuthComplete?.(false)
          navigate('/settings', { replace: true })
        }, 3000)
        
      } finally {
        // Clear the processing flag after a delay
        setTimeout(() => {
          isYahooOAuthProcessing = false
        }, 5000)
      }
    }
    
    handleCallback()
  }, [searchParams, hasProcessed, navigate, onAuthComplete])

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card className="bg-white/10 backdrop-blur-xl border-white/20 shadow-2xl">
          <CardContent className="p-8 text-center">
            {/* Yahoo Logo */}
            <div className="mb-6 flex justify-center">
              <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-2xl">Y!</span>
              </div>
            </div>
            
            {/* Status indicator */}
            <div className="mb-6">
              {status === 'processing' && (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-12 h-12 mx-auto border-4 border-purple-400 border-t-transparent rounded-full"
                />
              )}
              
              {status === 'success' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-12 h-12 mx-auto bg-green-500 rounded-full flex items-center justify-center"
                >
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>
              )}
              
              {status === 'error' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-12 h-12 mx-auto bg-red-500 rounded-full flex items-center justify-center"
                >
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </motion.div>
              )}
            </div>
            
            {/* Status message */}
            <h2 className="text-xl font-semibold text-white mb-2">
              {status === 'processing' && 'Connecting Yahoo Account...'}
              {status === 'success' && 'Yahoo Connected!'}
              {status === 'error' && 'Connection Failed'}
            </h2>
            
            <p className="text-white/70">
              {message}
            </p>
            
            {status === 'error' && (
              <button
                onClick={() => navigate('/settings')}
                className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                Return to Settings
              </button>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default YahooOAuthCallback
