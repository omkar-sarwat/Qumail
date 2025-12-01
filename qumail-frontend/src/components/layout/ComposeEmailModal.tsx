import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../ui/Button'

interface ComposeEmailModalProps {
  isOpen: boolean
  onClose: () => void
  onSent: () => void
  quantumKeysAvailable: number
}

export const ComposeEmailModal: React.FC<ComposeEmailModalProps> = ({
  isOpen,
  onClose,
  onSent,
  quantumKeysAvailable
}) => {
  const [formData, setFormData] = useState({
    to: '',
    cc: '',
    bcc: '',
    subject: '',
    body: '',
    securityLevel: 'quantum-otp',
    priority: 'normal'
  })
  const [isSending, setIsSending] = useState(false)

  const securityLevels = [
    {
      id: 'quantum-otp',
      name: 'Quantum OTP (Level 1)',
      description: 'One-time pad encryption with quantum keys',
      color: 'text-purple-600',
      available: quantumKeysAvailable > 0
    },
    {
      id: 'quantum-aes',
      name: 'Quantum AES (Level 2)',
      description: 'AES encryption with quantum-generated keys',
      color: 'text-blue-600',
      available: quantumKeysAvailable > 0
    },
    {
      id: 'post-quantum',
      name: 'Post-Quantum (Level 3)',
      description: 'Kyber + Dilithium cryptography',
      color: 'text-green-600',
      available: true
    },
    {
      id: 'standard',
      name: 'Standard RSA (Level 4)',
      description: 'RSA-4096 with AES-256-GCM',
      color: 'text-gray-600',
      available: true
    }
  ]

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSend = async () => {
    if (!formData.to || !formData.subject || !formData.body) {
      alert('Please fill in all required fields')
      return
    }

    setIsSending(true)
    try {
      const response = await fetch('https://qumail-backend-gwec.onrender.com/api/v1/emails/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          to: formData.to.split(',').map(email => email.trim()),
          cc: formData.cc ? formData.cc.split(',').map(email => email.trim()) : [],
          bcc: formData.bcc ? formData.bcc.split(',').map(email => email.trim()) : [],
          subject: formData.subject,
          body: formData.body,
          security_level: formData.securityLevel,
          priority: formData.priority
        })
      })

      if (response.ok) {
        onSent()
        setFormData({
          to: '',
          cc: '',
          bcc: '',
          subject: '',
          body: '',
          securityLevel: 'quantum-otp',
          priority: 'normal'
        })
      } else {
        const error = await response.json()
        alert(`Failed to send email: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to send email:', error)
      alert('Failed to send email. Please try again.')
    } finally {
      setIsSending(false)
    }
  }

  const selectedSecurity = securityLevels.find(level => level.id === formData.securityLevel)

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
            {/* Background overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              onClick={onClose}
            />

            {/* Modal panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative inline-block w-full max-w-4xl mx-auto overflow-hidden text-left align-middle transition-all transform bg-white dark:bg-gray-800 shadow-xl rounded-2xl"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Compose Quantum Email
                </h3>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Content */}
              <div className="px-6 py-4 max-h-96 overflow-y-auto">
                <div className="space-y-4">
                  {/* Recipients */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      To *
                    </label>
                    <input
                      type="email"
                      value={formData.to}
                      onChange={(e) => handleInputChange('to', e.target.value)}
                      placeholder="recipient@example.com"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>

                  {/* CC */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      CC
                    </label>
                    <input
                      type="email"
                      value={formData.cc}
                      onChange={(e) => handleInputChange('cc', e.target.value)}
                      placeholder="cc@example.com"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Subject */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Subject *
                    </label>
                    <input
                      type="text"
                      value={formData.subject}
                      onChange={(e) => handleInputChange('subject', e.target.value)}
                      placeholder="Email subject"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>

                  {/* Security Level */}
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Security Level
                    </label>
                    <select
                      value={formData.securityLevel}
                      onChange={(e) => handleInputChange('securityLevel', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {securityLevels.map((level) => (
                        <option 
                          key={level.id} 
                          value={level.id}
                          disabled={!level.available}
                        >
                          {level.name} - {level.description}
                        </option>
                      ))}
                    </select>
                    
                    {selectedSecurity && (
                      <div className={`mt-2 p-2 rounded-lg bg-opacity-10 ${selectedSecurity.color.replace('text-', 'bg-')}`}>
                        <div className={`flex items-center ${selectedSecurity.color}`}>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                          </svg>
                          <span className="text-sm font-medium">{selectedSecurity.name}</span>
                        </div>
                        <p className="text-xs mt-1 opacity-80">{selectedSecurity.description}</p>
                      </div>
                    )}
                  </div>

                  {/* Message Body */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Message *
                    </label>
                    <textarea
                      value={formData.body}
                      onChange={(e) => handleInputChange('body', e.target.value)}
                      placeholder="Type your quantum-secured message..."
                      rows={10}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  {quantumKeysAvailable} quantum keys available
                </div>
                
                <div className="flex space-x-3">
                  <Button
                    onClick={onClose}
                    variant="outline"
                    disabled={isSending}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSend}
                    disabled={isSending || !formData.to || !formData.subject || !formData.body}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {isSending ? (
                      <div className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
                          <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Sending...
                      </div>
                    ) : (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        Send Quantum Email
                      </div>
                    )}
                  </Button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  )
}