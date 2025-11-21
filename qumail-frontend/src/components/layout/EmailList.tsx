import React from 'react'
import { motion } from 'framer-motion'

interface Email {
  id: string
  sender: string
  subject: string
  snippet: string
  timestamp: string
  isRead: boolean
  isStarred: boolean
  securityLevel: string
  source: string
  labels?: string[]
}

interface EmailListProps {
  emails: Email[]
  selectedEmail: Email | null
  onEmailSelect: (email: Email) => void
  isLoading: boolean
  folderName: string
}

export const EmailList: React.FC<EmailListProps> = ({
  emails,
  selectedEmail,
  onEmailSelect,
  isLoading,
  folderName
}) => {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) return 'Today'
    if (diffDays === 2) return 'Yesterday'
    if (diffDays <= 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  const getSecurityIcon = (securityLevel: string) => {
    switch (securityLevel) {
      case 'quantum-otp':
        return (
          <div className="w-3.5 h-3.5 rounded-full bg-purple-500 flex items-center justify-center">
            <svg className="w-1.5 h-1.5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2L3 7v6c0 5.55 3.84 9.74 9 9.74s9-4.19 9-9.74V7l-7-5z" />
            </svg>
          </div>
        )
      case 'quantum-aes':
        return (
          <div className="w-3.5 h-3.5 rounded-full bg-blue-500 flex items-center justify-center">
            <svg className="w-1.5 h-1.5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2L3 7v6c0 5.55 3.84 9.74 9 9.74s9-4.19 9-9.74V7l-7-5z" />
            </svg>
          </div>
        )
      case 'post-quantum':
        return (
          <div className="w-3.5 h-3.5 rounded-full bg-green-500 flex items-center justify-center">
            <svg className="w-1.5 h-1.5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2L3 7v6c0 5.55 3.84 9.74 9 9.74s9-4.19 9-9.74V7l-7-5z" />
            </svg>
          </div>
        )
      default:
        return (
          <div className="w-3.5 h-3.5 rounded-full bg-gray-400 flex items-center justify-center">
            <svg className="w-1.5 h-1.5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2L3 7v6c0 5.55 3.84 9.74 9 9.74s9-4.19 9-9.74V7l-7-5z" />
            </svg>
          </div>
        )
    }
  }

  const getSourceIcon = (source: string) => {
    if (source === 'gmail') {
      return (
        <div className="w-3.5 h-3.5 text-red-500">
          <svg fill="currentColor" viewBox="0 0 24 24">
            <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-.904.732-1.636 1.636-1.636h3.819l6.545 4.91 6.545-4.91h3.819c.904 0 1.636.732 1.636 1.636z"/>
          </svg>
        </div>
      )
    }
    return (
      <div className="w-3.5 h-3.5 text-blue-600">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-6 w-6 text-blue-600 mx-auto mb-1.5" fill="none" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
            <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-xs text-gray-500 dark:text-gray-400">Loading emails...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center">
          <svg className="w-4 h-4 mr-1.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          {folderName}
          <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
            {emails.length}
          </span>
        </h2>
      </div>

      {/* Email List */}
      <div className="flex-1 overflow-y-auto">
        {emails.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center p-6">
            <div>
              <svg className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-1.5">No emails found</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">This folder is empty or no emails match your search.</p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {emails.map((email, index) => (
              <motion.div
                key={email.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onEmailSelect(email)}
                className={`cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150 ${
                  selectedEmail?.id === email.id 
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-blue-500' 
                    : ''
                }`}
              >
                <div className="px-3 py-2">
                  <div className="flex items-start justify-between mb-1.5">
                    <div className="flex items-center space-x-1.5 min-w-0 flex-1">
                      {getSourceIcon(email.source)}
                      <span className={`text-xs truncate ${
                        email.isRead 
                          ? 'text-gray-600 dark:text-gray-400' 
                          : 'font-semibold text-gray-900 dark:text-white'
                      }`}>
                        {email.sender}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1.5 flex-shrink-0">
                      {email.isStarred && (
                        <svg className="w-3.5 h-3.5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      )}
                      {getSecurityIcon(email.securityLevel)}
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatTimestamp(email.timestamp)}
                      </span>
                    </div>
                  </div>
                  
                  <h3 className={`text-xs mb-0.5 truncate ${
                    email.isRead 
                      ? 'text-gray-700 dark:text-gray-300' 
                      : 'font-semibold text-gray-900 dark:text-white'
                  }`}>
                    {email.subject || '(No Subject)'}
                  </h3>
                  
                  <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                    {email.snippet}
                  </p>
                  
                  {email.labels && email.labels.length > 0 && (
                    <div className="flex flex-wrap gap-0.5 mt-1.5">
                      {email.labels.slice(0, 3).map((label) => (
                        <span
                          key={label}
                          className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                        >
                          {label}
                        </span>
                      ))}
                      {email.labels.length > 3 && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          +{email.labels.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}