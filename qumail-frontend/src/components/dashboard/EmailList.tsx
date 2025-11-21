import React from 'react'
import { EmailListSkeleton } from '../ui/LoadingSpinner'

interface Email {
  id: string
  from?: string
  to?: string
  subject?: string
  body?: string
  html_body?: string
  plain_body?: string
  bodyText?: string
  bodyHtml?: string
  snippet?: string
  timestamp: string
  read?: boolean
  encrypted?: boolean
  securityLevel?: 1 | 2 | 3 | 4
  sender_name?: string
  sender_email?: string
  from_name?: string
  from_email?: string
  sender?: string
  recipient?: string
  messageId?: string
  threadId?: string
  cc?: string
  bcc?: string
  replyTo?: string
  isRead?: boolean
  isStarred?: boolean
  source?: string
  labels?: string[]
  hasAttachments?: boolean
  inlineImages?: boolean
  attachments?: Array<{
    id?: string
    name?: string
    filename?: string
    size: number
    type?: string
    mimeType?: string
    content?: string
    url?: string
  }>
}

interface EmailListProps {
  emails: Email[]
  selectedEmail: Email | null
  onEmailSelect: (email: Email) => void
  isLoading: boolean
  activeFolder: string
}

const CSS_MEDIA_BLOCK = /@[a-z\-]+[^{}]*\{[\s\S]*?\}/gi
const CSS_INLINE_BLOCK = /(?:^|\s)(?:[#.][\w-]+|[a-z0-9_-]+\s+[a-z0-9_.#-]+|body|html)[^{]*\{[^{}]*:[^{}]*\}/gi

const preferPreviewField = (email: Email) => {
  if (email.snippet && email.snippet.trim().length > 0) return email.snippet
  if (email.bodyText && email.bodyText.trim().length > 0) return email.bodyText
  if (email.body && email.body.trim().length > 0) return email.body
  if (email.plain_body && email.plain_body.trim().length > 0) return email.plain_body
  if (email.bodyHtml && email.bodyHtml.trim().length > 0) return email.bodyHtml
  if (email.html_body && email.html_body.trim().length > 0) return email.html_body
  return ''
}

const stripHtmlAndCss = (content: string) => {
  let sanitized = content
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(CSS_MEDIA_BLOCK, ' ')
    .replace(CSS_INLINE_BLOCK, ' ')
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<\/p>/gi, ' ')
    .replace(/<p[^>]*>/gi, ' ')
    .replace(/<div[^>]*>/gi, ' ')
    .replace(/<\/div>/gi, ' ')
    .replace(/<li[^>]*>/gi, '• ')
    .replace(/<\/li>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')

  sanitized = sanitized
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&hellip;/gi, '...')

  return sanitized.replace(/\s+/g, ' ').trim()
}

export const EmailList: React.FC<EmailListProps> = ({
  emails,
  selectedEmail,
  onEmailSelect,
  isLoading,
  activeFolder
}) => {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
      return 'Yesterday'
    } else if (days < 7) {
      return date.toLocaleDateString([], { weekday: 'short' })
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }
  }

  const getSecurityIcon = (level?: 1 | 2 | 3 | 4) => {
    // Default to level 4 (standard security) if undefined
    if (level === undefined) return getSecurityIcon(4)
    switch (level) {
      case 1:
        return (
          <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        )
      case 2:
        return (
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        )
      case 3:
        return (
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        )
      case 4:
        return (
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        )
    }
  }

  const getSecurityBadgeColor = (level?: 1 | 2 | 3 | 4) => {
    // Default to level 4 (standard security) if undefined
    if (level === undefined) return getSecurityBadgeColor(4)
    switch (level) {
      case 1:
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
      case 2:
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
      case 3:
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
      case 4:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300'
    }
  }

  const isUnreadEmail = (email: Email) => {
    const raw = email as any
    // Email is unread only if explicitly marked as unread and not marked as read
    const isExplicitlyRead = raw.read === true || raw.isRead === true || raw.is_read === true
    const isExplicitlyUnread = raw.read === false || raw.isRead === false || raw.is_read === false || raw.read_status === 'UNREAD'
    
    // If explicitly marked as read, return false (not unread)
    if (isExplicitlyRead) return false
    
    // If explicitly marked as unread, return true (is unread)
    if (isExplicitlyUnread) return true
    
    // Default to unread for new emails (safest assumption)
    return true
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  const getSenderInfo = (email: Email) => {
    // Try different fields for sender information with Gmail API fields
    const senderName = email.sender_name || email.from_name || 
      (email.sender && email.sender.includes('<') ? 
        email.sender.split('<')[0].trim().replace(/"/g, '') : 
        email.sender?.split('@')[0]) ||
      (email.from && email.from.includes('<') ? 
        email.from.split('<')[0].trim().replace(/"/g, '') : 
        email.from?.split('@')[0]) || 'Unknown Sender';
    
    const senderEmail = email.sender_email || email.from_email || 
      (email.sender && email.sender.includes('<') ? 
        email.sender.split('<')[1]?.replace('>', '').trim() : 
        email.sender) ||
      (email.from && email.from.includes('<') ? 
        email.from.split('<')[1]?.replace('>', '').trim() : 
        email.from) || '';
    
    return { senderName, senderEmail };
  }

  const getEmailContent = (email: Email) => {
    // Prefer sanitized snippet/plain text before HTML
    return preferPreviewField(email)
  }

  const getCleanPreviewText = (email: Email) => {
    const raw = email as any
    if (raw.body_encrypted || raw.requires_decryption || raw.encrypted || (raw.security_level && raw.security_level > 0)) {
      return '🔒 This email is quantum-encrypted. Click to view and decrypt.'
    }

    const content = getEmailContent(email)
    if (!content) return 'No content available'

    const textOnly = stripHtmlAndCss(content)
    const cleaned = textOnly.replace(/^(sent from|get outlook|sent via)/i, '').trim()

    return cleaned || 'No content available'
  }

  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white capitalize">
              {activeFolder}
            </h2>
            <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          </div>
        </div>

        {/* Professional Loading Skeleton */}
        <div className="flex-1 overflow-hidden">
          <EmailListSkeleton />
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#161b22] rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
      {/* Clean Professional Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-sm text-gray-900 dark:text-white capitalize">
              {activeFolder}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {emails.length} {emails.length === 1 ? 'email' : 'emails'}
            </p>
          </div>
          <button className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Clean Email List */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {emails.length === 0 ? (
          <div className="h-full flex items-center justify-center p-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                No emails
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Your {activeFolder} is empty
              </p>
            </div>
          </div>
        ) : (
          <div className="p-1">
            {emails.map((email) => (
              <div
                key={email.id}
                onClick={() => onEmailSelect(email)}
                className={`group relative px-3 py-3 cursor-pointer transition-colors border-l-2 rounded-r-lg mb-0.5 ${
                  selectedEmail?.id === email.id 
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-l-blue-600' 
                    : 'border-l-transparent hover:border-l-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800/50'
                } ${
                  isUnreadEmail(email) ? 'bg-white dark:bg-gray-800/50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Clean Avatar */}
                  <div className="flex-shrink-0 relative">
                    <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {(() => {
                          const { senderName } = getSenderInfo(email);
                          return senderName.charAt(0).toUpperCase();
                        })()}
                      </span>
                    </div>
                    {isUnreadEmail(email) && (
                      <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-blue-600 rounded-full"></div>
                    )}
                  </div>

                  {/* Email Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <p className={`text-base ${isUnreadEmail(email) ? 'font-bold text-gray-900 dark:text-white' : 'font-semibold text-gray-700 dark:text-gray-300'} truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors`}>
                          {getSenderInfo(email).senderName}
                        </p>
                        <div className="flex items-center space-x-2">
                          {((email.attachments && email.attachments.length > 0) || email.hasAttachments) && (
                            <div className="flex-shrink-0 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30 transition-colors">
                              <svg className="w-3 h-3 text-gray-500 group-hover:text-blue-600 dark:group-hover:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                              </svg>
                            </div>
                          )}
                          {email.isStarred && (
                            <div className="flex-shrink-0 p-1 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                              <svg className="w-3 h-3 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                              </svg>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 flex-shrink-0 ml-3">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30 transition-colors">
                          {formatTime(email.timestamp)}
                        </span>
                      </div>
                    </div>

                    <h3 className={`text-sm leading-tight ${isUnreadEmail(email) ? 'font-bold text-gray-900 dark:text-white' : 'font-semibold text-gray-700 dark:text-gray-300'} mb-2 truncate group-hover:text-blue-800 dark:group-hover:text-blue-200 transition-colors`}>
                      {email.subject || '(No Subject)'}
                    </h3>

                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3 leading-relaxed font-medium">
                      {(() => {
                        const content = getCleanPreviewText(email);
                        return content ? truncateText(content, 120) : 'No content available';
                      })()}
                    </p>

                    {/* Ultra-Modern Security Badges & Status Indicators */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm ${getSecurityBadgeColor(email.securityLevel)} group-hover:scale-105 transition-transform`}>
                          <svg className="w-3 h-3 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          {email.securityLevel ? 
                            (email.securityLevel === 1 ? 'QKD' : 
                             email.securityLevel === 2 ? 'Q-AES' : 
                             email.securityLevel === 3 ? 'PQC' : 'Standard') 
                            : 'Standard'}
                        </span>

                        {email.encrypted && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 dark:from-green-900/30 dark:to-emerald-900/30 dark:text-green-300 text-xs font-semibold shadow-sm group-hover:scale-105 transition-transform">
                            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                            </svg>
                            Encrypted
                          </span>
                        )}
                      </div>
                      
                      {/* Priority & Status Indicators */}
                      <div className="flex items-center space-x-1">
                        {isUnreadEmail(email) && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        )}
                        <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}