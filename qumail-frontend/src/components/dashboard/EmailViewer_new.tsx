import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '../ui/Button'

interface Email {
  id: string
  from?: string
  to?: string
  subject?: string
  body?: string
  timestamp: string
  read?: boolean
  encrypted?: boolean
  securityLevel?: 1 | 2 | 3 | 4
  attachments?: Array<{
    name: string
    size: number
    type: string
  }>
}

interface EmailViewerProps {
  email: Email | null
  onReply: () => void
  onReplyAll: () => void
  onForward: () => void
  onDelete: () => void
}

export const EmailViewer: React.FC<EmailViewerProps> = ({
  email,
  onReply,
  onReplyAll,
  onForward,
  onDelete
}) => {
  const [showSecurityDetails, setShowSecurityDetails] = useState(false);
  
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString([], {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSecurityDetails = (level?: 1 | 2 | 3 | 4) => {
    // Default to level 4 (standard security) if undefined
    if (level === undefined) return {
      label: 'Standard',
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-800',
      dotColor: 'bg-gray-400',
      hasDetailedInfo: false
    }
    
    switch (level) {
      case 1:
        return {
          label: 'Quantum OTP',
          bgColor: 'bg-purple-100',
          textColor: 'text-purple-800',
          dotColor: 'bg-purple-500',
          hasDetailedInfo: true
        }
      case 2:
        return {
          label: 'Q-AES',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          dotColor: 'bg-blue-500',
          hasDetailedInfo: false
        }
      case 3:
        return {
          label: 'Post-Quantum',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          dotColor: 'bg-green-500',
          hasDetailedInfo: false
        }
      case 4:
      default:
        return {
          label: 'Standard',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          dotColor: 'bg-gray-400',
          hasDetailedInfo: false
        }
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (!email) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <svg className="w-24 h-24 text-gray-300 dark:text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-2">
            Select an email to read
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Choose an email from the list to view its contents
          </p>
        </div>
      </div>
    )
  }

  const security = getSecurityDetails(email.securityLevel)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="h-full flex flex-col bg-white dark:bg-gray-800"
    >
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-700 p-6">
        {/* Action Buttons */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Button
              onClick={onReply}
              variant="ghost"
              size="sm"
              className="text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
              Reply
            </Button>
            <Button
              onClick={onReplyAll}
              variant="ghost"
              size="sm"
              className="text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6M14 6H8" />
              </svg>
              Reply All
            </Button>
            <Button
              onClick={onForward}
              variant="ghost"
              size="sm"
              className="text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              Forward
            </Button>
            <Button
              onClick={onDelete}
              variant="ghost"
              size="sm"
              className="text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </Button>
          </div>

          {/* Security Badge */}
          <div className="flex items-center">
            {email.securityLevel !== undefined && (
              <button 
                onClick={() => setShowSecurityDetails(!showSecurityDetails)}
                className={`px-3 py-1 text-xs font-semibold rounded-full flex items-center ${security.bgColor} ${security.textColor}`}
              >
                <span className={`w-2 h-2 rounded-full mr-2 ${security.dotColor}`}></span>
                {security.label}
                {security.hasDetailedInfo && (
                  <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </button>
            )}
            {email.encrypted && (
              <span
                className="ml-2 px-3 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full dark:bg-green-900 dark:text-green-200"
              >
                <svg className="inline w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Encrypted
              </span>
            )}
          </div>
        </div>

        {/* Subject */}
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {email.subject || "(No Subject)"}
        </h1>

        {/* Sender info & timestamp */}
        <div className="flex items-center space-x-4">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
              {email.from && typeof email.from === "string" ? email.from.charAt(0).toUpperCase() : "?"}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {email.from || "Unknown Sender"}
            </p>
            {email.from && typeof email.from === "string" && (
              <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                {email.from.split("@")[1] || "unknown"}
              </p>
            )}
          </div>
          <div className="text-right text-sm text-gray-500 dark:text-gray-400">
            {formatDate(email.timestamp)}
          </div>
        </div>

        {/* Recipients */}
        {email.to && (
          <div className="mt-3 text-sm text-gray-600 dark:text-gray-300">
            <span className="font-medium">To:</span> {email.to}
          </div>
        )}

        {/* Security Details Panel */}
        {showSecurityDetails && email.securityLevel === 1 && (
          <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg dark:bg-purple-900/20 dark:border-purple-800">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <svg className="h-5 w-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-purple-800 dark:text-purple-300">Quantum One-Time Pad Encryption</h3>
                <div className="mt-2 text-sm text-purple-700 dark:text-purple-400">
                  <p>
                    This email is secured with quantum one-time pad encryption, which is theoretically unbreakable due to its use of quantum key distribution (QKD).
                  </p>
                  <ul className="list-disc pl-5 mt-1 space-y-1">
                    <li>Keys generated using quantum mechanics principles</li>
                    <li>Perfect secrecy guaranteed by laws of physics</li>
                    <li>Immune to both classical and quantum computing attacks</li>
                    <li>Any tampering attempt would be immediately detected</li>
                  </ul>
                </div>
              </div>
              <button
                onClick={() => setShowSecurityDetails(false)}
                className="ml-auto flex-shrink-0 text-purple-500 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Email Body */}
      <div className="flex-1 overflow-auto p-6">
        <div className="prose dark:prose-invert max-w-none">
          {email.body || "(No content)"}
        </div>
      </div>

      {/* Attachments, if any */}
      {email.attachments && email.attachments.length > 0 && (
        <div className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-medium text-sm text-gray-900 dark:text-white mb-3">
            Attachments ({email.attachments.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {email.attachments.map((attachment, index) => (
              <div
                key={index}
                className="flex items-center p-2 bg-gray-50 dark:bg-gray-700 rounded-md"
              >
                <svg className="w-5 h-5 text-gray-500 dark:text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {attachment.name || "unnamed_file"}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {attachment.type || "unknown"}  {formatFileSize(attachment.size || 0)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default EmailViewer