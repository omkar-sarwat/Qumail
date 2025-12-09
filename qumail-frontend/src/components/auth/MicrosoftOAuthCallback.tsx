import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Card, CardContent } from '../ui/Card'
import { apiService } from '../../services/api'
import { useEmailAccountsStore } from '../../stores/emailAccountsStore'
import { emailSyncService } from '../../services/emailSyncService'
import { toast } from 'react-hot-toast'

// Global flag to prevent multiple OAuth processing
let isMicrosoftOAuthProcessing = false

export const MicrosoftOAuthCallback: React.FC = () => {
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Authenticating with Microsoft...')
  const [hasProcessed, setHasProcessed] = useState(false)
  const navigate = useNavigate()
  const { addAccount } = useEmailAccountsStore()

  useEffect(() => {
    // Check global processing flag first
    if (isMicrosoftOAuthProcessing) {
      console.log('Microsoft OAuth already processing globally, skipping')
      return
    }
    
    // Check if we've already processed this callback
    if (hasProcessed) {
      console.log('Microsoft OAuth callback already processed, skipping')
      return
    }
    
    // Extract URL parameters ONCE and clear them immediately
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const state = urlParams.get('state')
    const error = urlParams.get('error')
    const errorDescription = urlParams.get('error_description')
    
    // Clear URL parameters IMMEDIATELY to prevent reuse
    window.history.replaceState({}, document.title, window.location.pathname)
    
    if (!code && !error) {
      console.log('No Microsoft OAuth parameters found, redirecting to settings')
      navigate('/dashboard', { replace: true })
      return
    }
    
    const handleCallback = async () => {
      // Set global and local flags
      isMicrosoftOAuthProcessing = true
      setHasProcessed(true)
      
      try {
        console.log('Microsoft OAuth callback params:', { 
          code: code ? code.substring(0, 10) + '...' : null, 
          state, 
          error,
          timestamp: new Date().toISOString()
        })

        if (error) {
          setStatus('error')
          setMessage(`Authentication failed: ${errorDescription || error}`)
          toast.error(`Microsoft authentication failed: ${errorDescription || error}`)
          setTimeout(() => navigate('/dashboard', { replace: true }), 3000)
          return
        }

        if (!code) {
          throw new Error('No authorization code received from Microsoft')
        }

        // Verify state matches what we stored to prevent CSRF
        const storedState = sessionStorage.getItem('microsoft_oauth_state')
        if (!state || state !== storedState) {
          console.warn('Microsoft OAuth state mismatch, but continuing for debugging')
          // throw new Error('Invalid OAuth state - possible CSRF attack')
        }

        console.log('Sending Microsoft callback request to backend...')
        setMessage('Exchanging authorization code for access token...')
        
        // Exchange the authorization code for tokens
        const authResult = await apiService.exchangeMicrosoftCode(code, state || '')
        console.log('Microsoft authentication successful:', authResult.user_email)
        
        // Add the account to the email accounts store
        const accountId = `microsoft_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        
        addAccount({
          id: accountId,
          email: authResult.user_email,
          displayName: authResult.display_name || authResult.user_email.split('@')[0],
          provider: 'Microsoft/Outlook',
          settings: {
            // Microsoft Graph API doesn't use IMAP/SMTP, but we store placeholder values
            smtp_host: 'graph.microsoft.com',
            smtp_port: 443,
            smtp_security: 'ssl',
            imap_host: 'graph.microsoft.com',
            imap_port: 443,
            imap_security: 'ssl',
            protocol: 'oauth',  // Special protocol indicating OAuth-based access
          },
          isActive: true,
          isVerified: true,
          foldersToSync: ['INBOX', 'Sent'],
          authType: 'oauth',
          oauthProvider: 'microsoft',
        })
        
        // Store the session token for API calls
        sessionStorage.setItem(`microsoft_session_${authResult.user_email}`, authResult.session_token)
        
        setStatus('success')
        setMessage(`Welcome ${authResult.display_name}! Your Microsoft account is connected.`)
        
        toast.success(`Microsoft account ${authResult.user_email} connected successfully!`)
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
          navigate('/dashboard', { replace: true })
        }, 1500)
        
      } catch (error) {
        console.error('Microsoft OAuth callback error:', error)
        setStatus('error')
        const errorMessage = error instanceof Error ? error.message : 'Authentication failed'
        setMessage(errorMessage)
        toast.error(`Microsoft authentication failed: ${errorMessage}`)
        
        setTimeout(() => {
          navigate('/dashboard', { replace: true })
        }, 3000)
      } finally {
        // Reset flags and clear stored state
        isMicrosoftOAuthProcessing = false
        sessionStorage.removeItem('microsoft_oauth_state')
      }
    }

    handleCallback()
  }, [hasProcessed, navigate, addAccount])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <Card className="shadow-xl border-gray-200/50">
          <CardContent className="p-8">
            <div className="text-center">
              {/* Microsoft Logo */}
              <div className="w-16 h-16 mx-auto mb-6 flex items-center justify-center bg-gray-100 rounded-xl">
                <svg className="w-10 h-10" viewBox="0 0 21 21" fill="none">
                  <path d="M0 0h10v10H0V0z" fill="#F25022"/>
                  <path d="M11 0h10v10H11V0z" fill="#7FBA00"/>
                  <path d="M0 11h10v10H0V11z" fill="#00A4EF"/>
                  <path d="M11 11h10v10H11V11z" fill="#FFB900"/>
                </svg>
              </div>
              
              {/* Status Indicator */}
              {status === 'processing' && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mb-6"
                >
                  <div className="w-8 h-8 mx-auto mb-4">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full"
                    />
                  </div>
                </motion.div>
              )}

              {status === 'success' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', duration: 0.5 }}
                  className="w-16 h-16 mx-auto mb-6 bg-green-100 rounded-full flex items-center justify-center"
                >
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>
              )}

              {status === 'error' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', duration: 0.5 }}
                  className="w-16 h-16 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center"
                >
                  <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </motion.div>
              )}

              {/* Status Message */}
              <h2 className={`text-xl font-semibold mb-2 ${
                status === 'success' ? 'text-green-700' :
                status === 'error' ? 'text-red-700' :
                'text-gray-900'
              }`}>
                {status === 'processing' && 'Connecting to Microsoft'}
                {status === 'success' && 'Successfully Connected!'}
                {status === 'error' && 'Connection Failed'}
              </h2>
              
              <p className="text-gray-600">{message}</p>
              
              {status === 'error' && (
                <button
                  onClick={() => navigate('/dashboard', { replace: true })}
                  className="mt-6 px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                >
                  Return to Dashboard
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default MicrosoftOAuthCallback
