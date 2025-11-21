/**
 * DEMO: How to Use the New Compose Email Modal
 * 
 * This file demonstrates various ways to integrate and use the NewComposeEmailModal
 * in your QuMail application.
 */

import React, { useState } from 'react'
import { NewComposeEmailModal, QuantumSendSummary } from '../components/compose'
import toast from 'react-hot-toast'

// ============================================
// EXAMPLE 1: Basic Integration
// ============================================

export function BasicExample() {
  const [isComposeOpen, setIsComposeOpen] = useState(false)

  const handleSend = (summary: QuantumSendSummary) => {
    console.log('✉️ Email Sent Successfully!', summary)
    console.log('Flow ID:', summary.flowId)
    console.log('Security Level:', summary.securityLevel)
    console.log('Encryption Method:', summary.encryptionMethod)
    
    // Close the modal
    setIsComposeOpen(false)
    
    // Show success message (optional, modal already shows toast)
    toast.success('Your quantum-encrypted email has been sent!')
  }

  return (
    <div className="p-4">
      <button
        onClick={() => setIsComposeOpen(true)}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold shadow-lg"
      >
        ✉️ Compose New Email
      </button>

      <NewComposeEmailModal
        isOpen={isComposeOpen}
        onClose={() => setIsComposeOpen(false)}
        onSend={handleSend}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 2: Reply to Email
// ============================================

export function ReplyExample() {
  const [isReplyOpen, setIsReplyOpen] = useState(false)

  // Sample email to reply to
  const originalEmail = {
    id: '123',
    sender_email: 'alice@example.com',
    sender_name: 'Alice Johnson',
    subject: 'Project Update',
    body: 'Hi, just wanted to share the latest updates on the quantum encryption project...',
    timestamp: new Date().toISOString(),
    securityLevel: 2 as const
  }

  const handleReplySent = (summary: QuantumSendSummary) => {
    console.log('Reply sent:', summary)
    setIsReplyOpen(false)
    
    // Update UI, refresh thread, etc.
    toast.success('Reply sent successfully!')
  }

  return (
    <div className="p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 max-w-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {originalEmail.subject}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              From: {originalEmail.sender_name} &lt;{originalEmail.sender_email}&gt;
            </p>
          </div>
          <button
            onClick={() => setIsReplyOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Reply
          </button>
        </div>
        
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-gray-800 dark:text-gray-200">{originalEmail.body}</p>
        </div>
      </div>

      <NewComposeEmailModal
        isOpen={isReplyOpen}
        onClose={() => setIsReplyOpen(false)}
        onSend={handleReplySent}
        replyTo={originalEmail}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 3: Multiple Composers
// ============================================

export function MultipleComposersExample() {
  const [composeState, setComposeState] = useState<{
    type: 'new' | 'reply' | null
    email?: any
  }>({ type: null })

  const handleNewEmail = () => {
    setComposeState({ type: 'new' })
  }

  const handleReply = (email: any) => {
    setComposeState({ type: 'reply', email })
  }

  const handleClose = () => {
    setComposeState({ type: null })
  }

  const handleSend = (summary: QuantumSendSummary) => {
    console.log('Email sent:', summary)
    setComposeState({ type: null })
  }

  return (
    <div className="p-4">
      <div className="space-x-4">
        <button
          onClick={handleNewEmail}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          New Email
        </button>
        <button
          onClick={() => handleReply({ 
            id: '1', 
            sender_email: 'bob@example.com',
            sender_name: 'Bob Smith',
            subject: 'Hello',
            body: 'Test email',
            timestamp: new Date().toISOString()
          })}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Reply to Email
        </button>
      </div>

      <NewComposeEmailModal
        isOpen={composeState.type !== null}
        onClose={handleClose}
        onSend={handleSend}
        replyTo={composeState.type === 'reply' ? composeState.email : null}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 4: With State Management (Redux/Zustand)
// ============================================

// Using Zustand for state management
import { create } from 'zustand'

interface ComposeStore {
  isOpen: boolean
  replyTo: any | null
  openComposer: () => void
  openReply: (email: any) => void
  closeComposer: () => void
}

const useComposeStore = create<ComposeStore>((set) => ({
  isOpen: false,
  replyTo: null,
  openComposer: () => set({ isOpen: true, replyTo: null }),
  openReply: (email) => set({ isOpen: true, replyTo: email }),
  closeComposer: () => set({ isOpen: false, replyTo: null })
}))

export function StateManagementExample() {
  const { isOpen, replyTo, openComposer, openReply, closeComposer } = useComposeStore()

  const handleSend = (summary: QuantumSendSummary) => {
    console.log('Email sent:', summary)
    closeComposer()
    
    // Dispatch action to refresh inbox
    // dispatch(fetchEmails())
  }

  return (
    <div className="p-4">
      <div className="flex gap-3">
        <button
          onClick={openComposer}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Compose
        </button>
        <button
          onClick={() =>
            openReply({
              id: 'sample-reply',
              sender_email: 'alice@example.com',
              sender_name: 'Alice Quantum',
              subject: 'Follow-up on QKD session',
              body: 'Just checking in about the keys we exchanged.',
              timestamp: new Date().toISOString()
            })
          }
          className="px-4 py-2 bg-purple-600 text-white rounded-lg"
        >
          Reply to Sample
        </button>
      </div>

      <NewComposeEmailModal
        isOpen={isOpen}
        onClose={closeComposer}
        onSend={handleSend}
        replyTo={replyTo}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 5: Custom Send Handler with Error Handling
// ============================================

export function ErrorHandlingExample() {
  const [isOpen, setIsOpen] = useState(false)
  const [isSendingExternal, setIsSendingExternal] = useState(false)

  const handleSend = async (summary: QuantumSendSummary) => {
    setIsSendingExternal(true)
    
    try {
      // Additional processing after email is sent
      console.log('Processing send summary:', summary)
      
      // Maybe save to database
      // await saveToDatabase(summary)
      
      // Update UI
      // await refreshInbox()
      
      // Analytics
      // trackEmailSent(summary.securityLevel)
      
      console.log('✅ All post-send processing completed')
      setIsOpen(false)
      
      toast.success('Email sent and processed successfully!', {
        duration: 4000,
        icon: '🎉'
      })
      
    } catch (error) {
      console.error('Error in post-send processing:', error)
      toast.error('Email was sent but post-processing failed')
    } finally {
      setIsSendingExternal(false)
    }
  }

  return (
    <div className="p-4">
      <button
        onClick={() => setIsOpen(true)}
        disabled={isSendingExternal}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {isSendingExternal ? 'Processing...' : 'Compose Email'}
      </button>

      <NewComposeEmailModal
        isOpen={isOpen}
        onClose={() => !isSendingExternal && setIsOpen(false)}
        onSend={handleSend}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 6: Integration with Email Dashboard
// ============================================

export function DashboardIntegrationExample() {
  const [isComposeOpen, setIsComposeOpen] = useState(false)
  const [emails, setEmails] = useState<any[]>([])
  const [selectedEmail, setSelectedEmail] = useState<any | null>(null)

  const handleSend = (summary: QuantumSendSummary) => {
    console.log('Email sent:', summary)
    setIsComposeOpen(false)
    setSelectedEmail(null)
    
    // Refresh email list
    refreshEmails()
  }

  const refreshEmails = async () => {
    setEmails([
      {
        id: 'demo-1',
        subject: 'Quantum status update',
        sender_name: 'QuMail Bot',
        sender_email: 'bot@qumail.app',
        timestamp: new Date().toISOString()
      },
      {
        id: 'demo-2',
        subject: 'Team meeting notes',
        sender_name: 'Security Team',
        sender_email: 'security@example.com',
        timestamp: new Date().toISOString()
      }
    ])

    toast.success('Inbox refreshed!')
  }

  const handleReply = (email: any) => {
    setSelectedEmail(email)
    setIsComposeOpen(true)
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              📧 QuMail Dashboard
            </h1>
            <button
              onClick={() => {
                setSelectedEmail(null)
                setIsComposeOpen(true)
              }}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 font-semibold shadow-lg"
            >
              ✉️ Compose
            </button>
          </div>
        </div>

        {/* Email List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Inbox
          </h2>
          
          {emails.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
              No emails yet. Compose your first quantum-encrypted email!
            </p>
          ) : (
            <div className="space-y-2">
              {emails.map((email) => (
                <div
                  key={email.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {email.subject}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        From: {email.sender_name}
                      </p>
                    </div>
                    <button
                      onClick={() => handleReply(email)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Reply
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Composer Modal */}
      <NewComposeEmailModal
        isOpen={isComposeOpen}
        onClose={() => {
          setIsComposeOpen(false)
          setSelectedEmail(null)
        }}
        onSend={handleSend}
        replyTo={selectedEmail}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 7: Keyboard Shortcut Integration
// ============================================

export function KeyboardShortcutExample() {
  const [isOpen, setIsOpen] = useState(false)

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+M or Cmd+M to open composer
      if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
        e.preventDefault()
        setIsOpen(true)
      }
      
      // Escape to close (handled by modal, but good to know)
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  return (
    <div className="p-4">
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          💡 <strong>Tip:</strong> Press <kbd className="px-2 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded">Ctrl+M</kbd> to open the composer
        </p>
      </div>

      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg"
      >
        Open Composer
      </button>

      <NewComposeEmailModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onSend={(summary) => {
          console.log('Sent:', summary)
          setIsOpen(false)
        }}
      />
    </div>
  )
}

// ============================================
// EXAMPLE 8: Complete Demo App
// ============================================

export default function CompleteDemoApp() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            📧 QuMail Composer Demo
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Explore different ways to use the NewComposeEmailModal
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Example Cards */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              1️⃣ Basic Example
            </h3>
            <BasicExample />
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              2️⃣ Reply Example
            </h3>
            <ReplyExample />
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              5️⃣ Error Handling
            </h3>
            <ErrorHandlingExample />
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              7️⃣ Keyboard Shortcuts
            </h3>
            <KeyboardShortcutExample />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            6️⃣ Dashboard Integration
          </h3>
          <DashboardIntegrationExample />
        </div>
      </div>
    </div>
  )
}
