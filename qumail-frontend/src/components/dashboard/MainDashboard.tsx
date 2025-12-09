import React, { useCallback, useEffect, useMemo, useState, useRef, useLayoutEffect } from 'react'
import toast from 'react-hot-toast'
import { useAuth } from '../../context/AuthContext'
import { apiService } from '../../services/api'
import { useAuthStore } from '../../stores/authStore'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { EmailList } from './EmailList'
import { EmailViewer } from './EmailViewer'
import QuantumDashboard from './QuantumDashboard'
import { SettingsPanel } from './SettingsPanel'
import { NewComposeEmailModal, QuantumSendSummary } from '../compose/NewComposeEmailModal'
import { KeyVaultLogin, KeyManagerDashboard } from '../keymanager'
import { SyncedEmail } from '../../services/emailSyncService'
import { useEmailSyncStore } from '../../stores/emailSyncStore'

// Auto-refresh interval in milliseconds (30 seconds)
const AUTO_REFRESH_INTERVAL = 30000

type DashboardView = 'email' | 'quantum' | 'keymanager'

interface DashboardEmail extends Record<string, any> {
  id: string
  email_id?: string
  timestamp: string
  fullDate?: string
  subject?: string
  snippet?: string
  body?: string
  bodyHtml?: string
  bodyText?: string
  html_body?: string
  plain_body?: string
  body_encrypted?: string
  encrypted_size?: number
  securityLevel?: 0 | 1 | 2 | 3 | 4
  security_level?: 0 | 1 | 2 | 3 | 4
  sender?: string
  sender_name?: string
  sender_email?: string
  // CamelCase versions for EmailViewer component
  senderName?: string
  senderEmail?: string
  senderAvatar?: string
  from?: string
  from_name?: string
  from_email?: string
  to?: string
  recipient?: string
  encrypted?: boolean
  requires_decryption?: boolean
  isDecrypted?: boolean
  decrypted_body?: string
  decrypt_endpoint?: string
  flowId?: string
  flow_id?: string
  gmailMessageId?: string
  gmail_message_id?: string
  gmailThreadId?: string
  gmail_thread_id?: string
  encryptionMethod?: string
  encryption_method?: string
  encryption_metadata?: any
  attachments?: Array<Record<string, any>>
  read?: boolean
  isRead?: boolean
  is_read?: boolean
  isStarred?: boolean
  is_starred?: boolean
  tags?: string[]
  security_info?: {
    level?: number
    algorithm?: string
    quantum_enhanced?: boolean
    encrypted_size?: number
  }
}

const deriveDisplayName = (email?: string, name?: string) => {
  if (name && name.trim().length > 0) return name
  if (!email) return 'User'
  const prefix = email.split('@')[0]
  return prefix || email
}

const initialCounts = { inbox: 0, sent: 0, drafts: 0, trash: 0 }

const generateId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return Math.random().toString(36).slice(2)
}

export const MainDashboard: React.FC = () => {
  const { user, isAuthenticated } = useAuth()
  const initialLoadRef = useRef(true)
  const [isReady, setIsReady] = useState(false)

  const [currentView, setCurrentView] = useState<DashboardView>('email')
  const [activeFolder, setActiveFolder] = useState('inbox')
  const [emails, setEmails] = useState<DashboardEmail[]>([])
  const [selectedEmail, setSelectedEmail] = useState<DashboardEmail | null>(null)
  const [isLoadingEmails, setIsLoadingEmails] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [emailCounts, setEmailCounts] = useState(initialCounts)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isComposeOpen, setIsComposeOpen] = useState(false)
  const [replyToEmail, setReplyToEmail] = useState<DashboardEmail | null>(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [selectedSecurityLevels, setSelectedSecurityLevels] = useState<Set<number>>(new Set([1, 2, 3, 4]))

  // Get provider emails from sync store
  const syncStore = useEmailSyncStore()
  const providerEmails = syncStore.getAllEmails()

  // Mark component as ready after first paint to prevent flickering
  useLayoutEffect(() => {
    if (initialLoadRef.current) {
      initialLoadRef.current = false
      // Use requestAnimationFrame to wait for paint
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setIsReady(true)
        })
      })
    }
  }, [])
  
  // Key Manager auth state
  const [keyManagerAuth, setKeyManagerAuth] = useState<{
    isLoggedIn: boolean
    kmType: 'KM1' | 'KM2' | null
    username: string | null
  }>({
    isLoggedIn: false,
    kmType: null,
    username: null,
  })

  const handleKeyManagerLogin = (kmType: 'KM1' | 'KM2', username: string) => {
    setKeyManagerAuth({
      isLoggedIn: true,
      kmType,
      username,
    })
  }

  const handleKeyManagerLogout = () => {
    setKeyManagerAuth({
      isLoggedIn: false,
      kmType: null,
      username: null,
    })
    setCurrentView('email')
  }

  const normalizeEmail = useCallback((raw: any): DashboardEmail => {
    if (!raw) {
      return {
        id: generateId(),
        timestamp: new Date().toISOString(),
      }
    }

    const baseId = raw.id ?? raw.email_id ?? raw.gmailMessageId ?? raw.messageId ?? raw.uuid ?? raw.uid
    const resolvedId = baseId ? String(baseId) : generateId()

    const senderEmail = raw.sender_email ?? raw.from_email ?? raw.fromAddress ?? raw.from ?? ''
    const inferredSenderEmail = senderEmail || (typeof raw.sender === 'string' && raw.sender.includes('<')
      ? raw.sender.split('<')[1]?.replace('>', '').trim()
      : raw.sender)
    const finalSenderEmail = inferredSenderEmail || (typeof raw.from === 'string' && raw.from.includes('<')
      ? raw.from.split('<')[1]?.replace('>', '').trim()
      : raw.from)

    const senderName = raw.sender_name ?? raw.from_name ?? (() => {
      if (typeof raw.sender === 'string' && raw.sender.includes('<')) {
        return raw.sender.split('<')[0].trim().replace(/"/g, '')
      }
      if (typeof raw.from === 'string' && raw.from.includes('<')) {
        return raw.from.split('<')[0].trim().replace(/"/g, '')
      }
      if (raw.sender) return raw.sender.split('@')[0]
      if (raw.from) return raw.from.split('@')[0]
      if (finalSenderEmail) return finalSenderEmail.split('@')[0]
      return 'Unknown Sender'
    })()

    const toAddress = raw.to ?? raw.toAddress ?? raw.recipient ?? raw.receiver_email ?? ''

    const timestampSource = raw.timestamp ?? raw.date ?? raw.sentAt ?? raw.receivedAt ?? raw.internalDate
    const timestamp = timestampSource ? new Date(timestampSource).toISOString() : new Date().toISOString()

    // Don't default security level to 4 - use 0 for non-quantum emails
    const securityLevel = (raw.security_level ?? raw.securityLevel ?? raw.security_info?.level ?? 0) as 0 | 1 | 2 | 3 | 4
    const flowId = raw.flow_id ?? raw.flowId ?? raw.encryption_metadata?.flow_id ?? raw.encryption_metadata?.flowId ?? ''
    const gmailMessageId = raw.gmail_message_id ?? raw.gmailMessageId ?? raw.messageId ?? null
    const gmailThreadId = raw.gmail_thread_id ?? raw.gmailThreadId ?? raw.threadId ?? null

    const bodyHtml = raw.bodyHtml ?? raw.html_body ?? null
    const bodyText = raw.bodyText ?? raw.body ?? raw.plain_body ?? raw.snippet ?? ''
    const encryptedBody = raw.body_encrypted ?? raw.encrypted_body ?? ''
    const encryptionMetadata = raw.encryption_metadata ?? raw.encryptionMetadata ?? null
    const encryptionMethod = raw.encryption_method ?? raw.encryptionMethod ?? encryptionMetadata?.algorithm ?? null

    const subjectText = String(raw.subject ?? '').toLowerCase()
    const snippetText = String(raw.snippet ?? '').toLowerCase()
    const combinedBody = `${bodyText ?? ''} ${bodyHtml ?? ''}`.toLowerCase()
    const looksQuantumBySubject = subjectText.includes('[quantum') || subjectText.includes('quantum-secured')
    const looksQuantumByContent = combinedBody.includes('quantum-encrypted email') || combinedBody.includes('encrypted content (base64 ciphertext)') || combinedBody.includes('quantum aes-256-gcm')
    const looksQuantumBySnippet = snippetText.includes('quantum-encrypted') || snippetText.includes('qkd')
    const algorithmText = (raw.security_info?.algorithm ?? encryptionMethod ?? '').toLowerCase()
    const hasQuantumSecurityFlag = Boolean(raw.security_info?.quantum_enhanced || algorithmText.includes('quantum') || algorithmText.includes('qkd'))
    const requiresDecryption =
      raw.requires_decryption ??
      raw.requiresDecryption ??
      Boolean(
        !raw.isDecrypted && // If already decrypted, don't require decryption
        (
          (encryptedBody && encryptedBody.trim().length > 0) ||
          encryptionMetadata ||
          raw.encrypted ||
          looksQuantumBySubject ||
          looksQuantumByContent ||
          looksQuantumBySnippet ||
          hasQuantumSecurityFlag
        )
      )

    const attachmentsRaw = Array.isArray(raw.attachments)
      ? raw.attachments
      : Array.isArray(raw.attachments_metadata)
        ? raw.attachments_metadata
        : []

    const normalizedAttachments = attachmentsRaw.map((attachment: any) => ({
      ...attachment,
      id: attachment.id ?? attachment.attachmentId ?? attachment.partId ?? generateId(),
      name: attachment.name ?? attachment.filename ?? attachment.fileName ?? 'attachment',
      filename: attachment.filename ?? attachment.name ?? attachment.fileName ?? 'attachment',
      size: attachment.size ?? attachment.bodySize ?? 0,
      mimeType: attachment.mimeType ?? attachment.type ?? 'application/octet-stream',
    }))

    const securityInfo = raw.security_info ?? {
      level: securityLevel,
      algorithm: encryptionMethod ?? 'Unknown',
      quantum_enhanced: raw.security_info?.quantum_enhanced ?? true,
      encrypted_size: raw.encrypted_size ?? raw.encryptedSize ?? raw.security_info?.encrypted_size ?? 0,
    }

    const tags: string[] = []
    const hasEncryptedPayload = Boolean(encryptedBody && encryptedBody.trim().length > 0)

    if (
      securityLevel > 0 ||
      looksQuantumBySubject ||
      looksQuantumByContent ||
      looksQuantumBySnippet ||
      hasQuantumSecurityFlag ||
      hasEncryptedPayload ||
      requiresDecryption
    ) {
      tags.push('QUANTUM')
    } else {
      tags.push('STD')
    }

    return {
      ...raw,
      id: resolvedId,
      email_id: raw.email_id ?? resolvedId,
      subject: raw.subject ?? '(No Subject)',
      snippet: raw.snippet ?? bodyText?.slice(0, 140) ?? '',
      body: raw.body ?? bodyText ?? '',
      bodyText,
      bodyHtml,
      html_body: bodyHtml ?? undefined,
      plain_body: raw.plain_body ?? bodyText ?? '',
      body_encrypted: encryptedBody,
      encrypted_size: raw.encrypted_size ?? raw.encryptedSize ?? 0,
      timestamp,
      // Format timestamp for display
      fullDate: new Date(timestamp).toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      }),
      securityLevel,
      security_level: securityLevel,
      to: toAddress,
      recipient: raw.recipient ?? toAddress,
      sender: raw.sender ?? (finalSenderEmail ? `${senderName} <${finalSenderEmail}>` : senderName),
      sender_name: senderName,
      sender_email: finalSenderEmail ?? '',
      // Add camelCase versions for EmailViewer component
      senderName: senderName,
      senderEmail: finalSenderEmail ?? '',
      senderAvatar: senderName?.[0]?.toUpperCase() ?? '?',
      from: raw.from ?? (finalSenderEmail ? `${senderName} <${finalSenderEmail}>` : senderName),
      from_name: raw.from_name ?? senderName,
      from_email: raw.from_email ?? finalSenderEmail ?? '',
      receiver_email: raw.receiver_email ?? toAddress,
      encrypted: raw.encrypted ?? requiresDecryption,
      requires_decryption: requiresDecryption,
      isDecrypted: raw.isDecrypted ?? false, // Preserve decrypted state
      decrypt_endpoint: raw.decrypt_endpoint ?? `/api/v1/emails/email/${resolvedId}/decrypt`,
      flowId,
      flow_id: flowId,
      gmailMessageId,
      gmail_message_id: gmailMessageId,
      gmailThreadId,
      gmail_thread_id: gmailThreadId,
      encryptionMethod,
      encryption_method: encryptionMethod,
      encryption_metadata: encryptionMetadata,
      sent_via_gmail: raw.sent_via_gmail ?? encryptionMetadata?.sent_via_gmail,
      attachments: normalizedAttachments,
      read: raw.read ?? raw.isRead ?? raw.is_read ?? true,
      isRead: raw.isRead ?? raw.read ?? raw.is_read ?? true,
      is_read: raw.is_read ?? raw.isRead ?? raw.read ?? true,
      isStarred: raw.isStarred ?? raw.is_starred ?? false,
      is_starred: raw.is_starred ?? raw.isStarred ?? false,
      security_info: securityInfo,
      tags,
    }
  }, [])

  const fetchEmailCounts = useCallback(async () => {
    try {
      const folders = await apiService.getEmailFolders().catch(() => [])
      if (!Array.isArray(folders)) {
        setEmailCounts(initialCounts)
        return
      }

      const counts = folders.reduce(
        (acc, folder: any) => {
          const id = String(folder.id ?? folder.name ?? '').toLowerCase()
          const value = Number(folder.count ?? folder.total ?? 0)

          if (id.includes('inbox')) acc.inbox = value
          if (id.includes('sent')) acc.sent = value
          if (id.includes('draft')) acc.drafts = value
          if (id.includes('trash') || id.includes('bin')) acc.trash = value

          return acc
        },
        { ...initialCounts }
      )

      setEmailCounts(counts)
    } catch (error) {
      console.error('Failed to fetch email counts:', error)
      setEmailCounts(initialCounts)
    }
  }, [])

  const loadEmailDetails = useCallback(
    async (emailId: string, fallback?: DashboardEmail) => {
      try {
        console.log('📧 Loading email details for:', emailId)
        const details = await apiService.getEmailDetails(emailId)
        console.log('📥 Received email details from backend:', {
          flow_id: details.flow_id,
          security_level: details.security_level,
          encrypted_size: details.encrypted_size,
          security_info: details.security_info,
          encryption_metadata: details.encryption_metadata,
          requires_decryption: details.requires_decryption,
          body_encrypted: details.body_encrypted ? `${details.body_encrypted.substring(0, 50)}...` : null
        })

        const normalized = normalizeEmail({ ...fallback, ...details })
        console.log('🔄 Normalized email:', {
          id: normalized.id,
          flow_id: normalized.flow_id,
          security_level: normalized.security_level,
          encrypted_size: normalized.encrypted_size,
          security_info: normalized.security_info,
          requires_decryption: normalized.requires_decryption,
          body_encrypted: normalized.body_encrypted ? `${normalized.body_encrypted.substring(0, 50)}...` : null
        })

        setSelectedEmail(normalized)

        setEmails((current) =>
          current.map((email) => (email.id === normalized.id ? normalized : email))
        )

        if (!normalized.isRead) {
          await apiService.markEmailAsRead(normalized.id, true).catch(() => undefined)
          setEmails((current) =>
            current.map((email) =>
              email.id === normalized.id ? { ...email, isRead: true, read: true, is_read: true } : email
            )
          )
        }
      } catch (error) {
        console.error('Failed to load email details:', error)
        toast.error('Failed to load full email content')
      }
    },
    [normalizeEmail]
  )

  const fetchEmails = useCallback(
    async (folder: string) => {
      setIsLoadingEmails(true)
      try {
        const response = await apiService.getEmails({ folder: folder as any, maxResults: 50 })
        const mapped = Array.isArray(response.emails)
          ? response.emails.map((email) => normalizeEmail(email))
          : []

        setEmails(mapped)

        if (mapped.length > 0) {
          const initialEmail = mapped[0]
          setSelectedEmail(initialEmail)
          loadEmailDetails(initialEmail.id, initialEmail)
        } else {
          setSelectedEmail(null)
        }
      } catch (error) {
        console.error('Failed to fetch emails:', error)
        toast.error('Failed to load emails')
        setEmails([])
        setSelectedEmail(null)
      } finally {
        setIsLoadingEmails(false)
      }
    },
    [loadEmailDetails, normalizeEmail]
  )

  // Silent refresh - fetches new emails without showing loading state or changing selection
  const silentRefreshEmails = useCallback(
    async (folder: string) => {
      try {
        const response = await apiService.getEmails({ folder: folder as any, maxResults: 50 })
        const newEmails = Array.isArray(response.emails)
          ? response.emails.map((email) => normalizeEmail(email))
          : []

        setEmails(prevEmails => {
          // Preserve decrypted state for emails we already have
          const emailMap = new Map(prevEmails.map(e => [e.id, e]))
          
          return newEmails.map(newEmail => {
            const existingEmail = emailMap.get(newEmail.id)
            if (existingEmail?.isDecrypted) {
              // Keep the decrypted content
              return {
                ...newEmail,
                body: existingEmail.body,
                bodyHtml: existingEmail.bodyHtml,
                bodyText: existingEmail.bodyText,
                content: existingEmail.content,
                requires_decryption: false,
                isEncrypted: false,
                isDecrypted: true,
              }
            }
            return newEmail
          })
        })

        // Check if there are new emails (not in previous list)
        setEmails(prevEmails => {
          const prevIds = new Set(prevEmails.map(e => e.id))
          const hasNewEmails = newEmails.some(e => !prevIds.has(e.id))
          
          if (hasNewEmails) {
            // Show a subtle notification for new emails
            const newCount = newEmails.filter(e => !prevIds.has(e.id)).length
            if (newCount > 0) {
              toast.success(`${newCount} new email${newCount > 1 ? 's' : ''} received`, {
                duration: 3000,
                icon: '📬',
              })
            }
          }
          
          return prevEmails // Don't change state here, already updated above
        })

        // Also refresh counts
        fetchEmailCounts()
      } catch (error) {
        // Silent fail - don't show error for background refresh
        console.error('Silent refresh failed:', error)
      }
    },
    [normalizeEmail, fetchEmailCounts]
  )

  // Manual refresh handler with loading indicator
  const handleManualRefresh = useCallback(async () => {
    if (isRefreshing) return
    setIsRefreshing(true)
    try {
      await silentRefreshEmails(activeFolder)
      toast.success('Emails refreshed', { duration: 2000, icon: '✓' })
    } finally {
      setIsRefreshing(false)
    }
  }, [isRefreshing, silentRefreshEmails, activeFolder])

  const handleEmailSelect = useCallback(
    (email: DashboardEmail) => {
      setCurrentView('email')
      
      // Check if we already have a decrypted version in the emails list
      const existingEmail = emails.find(e => e.id === email.id)
      const emailToSelect = existingEmail?.isDecrypted ? existingEmail : email
      
      setSelectedEmail(emailToSelect)

      // Immediately mark as read in local state to remove red dot
      if (!emailToSelect.isRead && !emailToSelect.read) {
        setEmails(current =>
          current.map(e =>
            e.id === emailToSelect.id ? { ...e, isRead: true, read: true, is_read: true } : e
          )
        )
      }

      // Only load details if not already decrypted
      if (!emailToSelect.isDecrypted) {
        loadEmailDetails(emailToSelect.id, emailToSelect)
      }
    },
    [loadEmailDetails, emails]
  )

  const handleFolderChange = useCallback((folder: string) => {
    setCurrentView('email')
    setActiveFolder(folder)
    setSelectedEmail(null)
  }, [])

  const handleCompose = useCallback(() => {
    setReplyToEmail(null)
    setIsComposeOpen(true)
  }, [])

  const handleReply = useCallback(() => {
    if (!selectedEmail) return
    setReplyToEmail(selectedEmail)
    setIsComposeOpen(true)
  }, [selectedEmail])

  const handleReplyAll = useCallback(() => {
    if (!selectedEmail) return
    setReplyToEmail(selectedEmail)
    setIsComposeOpen(true)
  }, [selectedEmail])

  const handleForward = useCallback(() => {
    if (!selectedEmail) return
    setReplyToEmail(selectedEmail)
    setIsComposeOpen(true)
  }, [selectedEmail])

  const handleSecurityLevelToggle = useCallback((level: number) => {
    setSelectedSecurityLevels(prev => {
      const newSet = new Set(prev)
      if (newSet.has(level)) {
        newSet.delete(level)
      } else {
        newSet.add(level)
      }
      // If all are unchecked, default to showing all levels 1-4
      if (newSet.size === 0) {
        return new Set([1, 2, 3, 4])
      }
      return newSet
    })
  }, [])

  const handleEmailDecrypted = useCallback((result: { email_data: any; security_info?: any }) => {
    const decrypted = result?.email_data
    if (!decrypted) return

    setEmails(current => current.map(email => {
      if (email.id !== decrypted.email_id && email.email_id !== decrypted.email_id) {
        return email
      }

      return {
        ...email,
        id: email.id ?? decrypted.email_id,
        email_id: decrypted.email_id,
        body: decrypted.body,
        bodyHtml: decrypted.body,
        bodyText: decrypted.body,
        content: decrypted.body,
        requires_decryption: false,
        isEncrypted: false,
        isDecrypted: true,
        securityLevel: result.security_info?.security_level ?? email.securityLevel,
        security_info: result.security_info ?? email.security_info,
        attachments: decrypted.attachments ?? email.attachments,
      }
    }))

    setSelectedEmail(prev => {
      if (!prev) return prev
      if (prev.id !== decrypted.email_id && prev.email_id !== decrypted.email_id) {
        return prev
      }

      return {
        ...prev,
        email_id: decrypted.email_id,
        body: decrypted.body,
        bodyHtml: decrypted.body,
        bodyText: decrypted.body,
        content: decrypted.body,
        requires_decryption: false,
        isEncrypted: false,
        isDecrypted: true,
        securityLevel: result.security_info?.security_level ?? prev.securityLevel,
        security_info: result.security_info ?? prev.security_info,
        attachments: decrypted.attachments ?? prev.attachments,
      }
    })
  }, [])

  const handleDeleteEmail = useCallback(async () => {
    if (!selectedEmail) return

    try {
      if (activeFolder === 'trash') {
        await apiService.deleteEmail(selectedEmail.id)
      } else {
        await apiService.moveEmailToTrash(selectedEmail.id)
      }

      toast.success(activeFolder === 'trash' ? 'Email deleted' : 'Moved to trash')
      await fetchEmails(activeFolder)
      await fetchEmailCounts()
    } catch (error) {
      console.error('Failed to remove email:', error)
      toast.error('Failed to delete email')
    }
  }, [activeFolder, fetchEmailCounts, fetchEmails, selectedEmail])

  const handleEmailSent = useCallback(
    (summary: QuantumSendSummary) => {
      toast.success(summary.message || 'Encrypted email sent')
      setIsComposeOpen(false)
      setReplyToEmail(null)
      fetchEmails(activeFolder)
      fetchEmailCounts()
    },
    [activeFolder, fetchEmailCounts, fetchEmails]
  )

  const handleSidebarToggle = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev)
  }, [])

  const handleToggleStar = useCallback(
    async (emailId: string) => {
      const currentEmail = emails.find((email) => email.id === emailId)
      if (!currentEmail) return

      const originalStar = Boolean(currentEmail.isStarred ?? currentEmail.is_starred)
      const nextStar = !originalStar

      setEmails((current) =>
        current.map((email) =>
          email.id === emailId ? { ...email, isStarred: nextStar, is_starred: nextStar } : email
        )
      )

      setSelectedEmail((prev) =>
        prev && prev.id === emailId ? { ...prev, isStarred: nextStar, is_starred: nextStar } : prev
      )

      try {
        await apiService.toggleEmailStar(emailId, nextStar)
        toast.success(nextStar ? 'Added to starred' : 'Removed from starred')
      } catch (error) {
        console.error('Failed to toggle star:', error)
        toast.error('Failed to update star status')

        setEmails((current) =>
          current.map((email) =>
            email.id === emailId ? { ...email, isStarred: originalStar, is_starred: originalStar } : email
          )
        )

        setSelectedEmail((prev) =>
          prev && prev.id === emailId ? { ...prev, isStarred: originalStar, is_starred: originalStar } : prev
        )
      }
    },
    [emails]
  )

  // Convert provider emails to DashboardEmail format for unified inbox
  const convertProviderEmail = useCallback((email: SyncedEmail): DashboardEmail => {
    return {
      id: `provider_${email.id}`,
      email_id: email.id,
      timestamp: email.timestamp,
      subject: email.subject,
      snippet: email.body_text?.slice(0, 140) || '',
      body: email.body_text,
      bodyHtml: email.body_html || undefined,
      bodyText: email.body_text,
      sender: email.from_name || email.from_address,
      sender_name: email.from_name,
      sender_email: email.from_address,
      senderName: email.from_name,
      senderEmail: email.from_address,
      to: email.to_address,
      recipient: email.to_address,
      isRead: email.is_read,
      is_read: email.is_read,
      read: email.is_read,
      securityLevel: 0,
      encrypted: false,
      requires_decryption: false,
      isDecrypted: true,
      tags: ['PROVIDER'],
      source: 'provider',
    }
  }, [])

  const filteredEmails = useMemo(() => {
    // Start with Gmail/QuMail emails
    let filtered = [...emails]

    // When viewing inbox, merge in provider emails
    if (activeFolder === 'inbox') {
      const providerDashboardEmails = providerEmails.map(convertProviderEmail)
      filtered = [...filtered, ...providerDashboardEmails]
      
      // Sort all emails by timestamp descending
      filtered.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )
    }

    // Filter by security level (1-4 are quantum encrypted levels)
    // When all 4 levels are selected, show all emails including unencrypted
    const allLevelsSelected = selectedSecurityLevels.size === 4 && 
      selectedSecurityLevels.has(1) && selectedSecurityLevels.has(2) && 
      selectedSecurityLevels.has(3) && selectedSecurityLevels.has(4)
    
    if (!allLevelsSelected) {
      filtered = filtered.filter(email => {
        const level = email.securityLevel ?? email.security_level ?? 0
        return selectedSecurityLevels.has(level)
      })
    }

    // Then filter by search query if present
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter((email) => {
        const fields = [
          email.subject,
          email.snippet,
          email.bodyText,
          email.sender_name,
          email.sender_email,
          email.from,
          email.to,
        ]
        return fields.some((field) => field && String(field).toLowerCase().includes(query))
      })
    }

    return filtered
  }, [emails, searchQuery, selectedSecurityLevels, activeFolder, providerEmails, convertProviderEmail])

  useEffect(() => {
    // Check for token in localStorage (legacy) OR in Zustand store
    const legacyToken = localStorage.getItem('authToken')
    const zustandAuth = localStorage.getItem('qumail-auth')
    
    // Try to get token from Zustand's persisted storage
    let zustandToken: string | null = null
    if (zustandAuth) {
      try {
        const parsed = JSON.parse(zustandAuth)
        zustandToken = parsed?.state?.sessionToken || null
      } catch (e) {
        console.warn('Failed to parse qumail-auth:', e)
      }
    }
    
    // Use whichever token is available
    const token = legacyToken || zustandToken
    
    if (!token) {
      // CRITICAL: Only clear auth if we're ONLINE
      // When offline, trust the Zustand store's persisted state
      if (navigator.onLine) {
        console.log('🔑 [MainDashboard] No token found and online - clearing auth')
        apiService.clearAuthToken()
        useAuthStore.setState((state) => ({
          ...state,
          sessionToken: null,
          isAuthenticated: false,
        }))
      } else {
        console.log('📴 [MainDashboard] No legacy token but offline - checking Zustand state')
        // Don't clear! Trust the Zustand persisted state
        const currentState = useAuthStore.getState()
        if (currentState.user && currentState.sessionToken) {
          console.log('✅ [MainDashboard] Zustand has valid auth - keeping authenticated')
        }
      }
      return
    }

    console.log('🔑 [MainDashboard] Token found - setting auth')
    apiService.setAuthToken(token)

    useAuthStore.setState((state) => {
      if (state.sessionToken === token && state.isAuthenticated) {
        return state
      }

      return {
        ...state,
        sessionToken: token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        user:
          state.user ||
          (user
            ? {
              email: user.email,
              displayName: deriveDisplayName(user.email, user.name),
              createdAt: new Date().toISOString(),
              oauthConnected: true,
              lastLogin: new Date().toISOString(),
            }
            : state.user),
      }
    })
  }, [isAuthenticated, user?.email, user?.name])

  useEffect(() => {
    fetchEmailCounts()
  }, [fetchEmailCounts])

  useEffect(() => {
    fetchEmails(activeFolder)
  }, [activeFolder, fetchEmails])

  // Auto-refresh emails every 30 seconds
  useEffect(() => {
    // Set up interval for auto-refresh
    const intervalId = setInterval(() => {
      silentRefreshEmails(activeFolder)
    }, AUTO_REFRESH_INTERVAL)

    // Also refresh when window regains focus
    const handleFocus = () => {
      silentRefreshEmails(activeFolder)
    }
    
    window.addEventListener('focus', handleFocus)

    // Cleanup on unmount or when activeFolder changes
    return () => {
      clearInterval(intervalId)
      window.removeEventListener('focus', handleFocus)
    }
  }, [activeFolder, silentRefreshEmails])


  const headerUser = user
    ? {
      id: user.email,
      email: user.email,
      name: deriveDisplayName(user.email, user.name),
      picture: (user as any)?.picture,
    }
    : null

  return (
    <div className={`flex-1 flex flex-col bg-gray-50 overflow-hidden h-full transition-opacity duration-150 ${isReady ? 'opacity-100' : 'opacity-0'}`}>
      <Header
        user={headerUser}
        onCompose={handleCompose}
        onSettings={() => setIsSettingsOpen(true)}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        currentView={currentView}
        onViewChange={setCurrentView}
        onToggleSidebar={handleSidebarToggle}
        isSidebarCollapsed={isSidebarCollapsed}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      <div className="flex-1 flex overflow-hidden py-3 pr-3 pl-0 gap-3">
        <div className="flex-shrink-0 h-full">
          <Sidebar
            activeFolder={activeFolder}
            onFolderChange={handleFolderChange}
            onCompose={handleCompose}
            emailCounts={emailCounts}
            onNavigateToView={(view) => setCurrentView(view as DashboardView)}
            onOpenSettings={() => setIsSettingsOpen(true)}
            isCompact={isSidebarCollapsed}
            currentView={currentView}
            keyManagerLoggedIn={keyManagerAuth.isLoggedIn}
            keyManagerType={keyManagerAuth.kmType}
            selectedSecurityLevels={selectedSecurityLevels}
            onSecurityLevelToggle={handleSecurityLevelToggle}
            emails={emails}
          />
        </div>

        {currentView === 'email' ? (
          <>
            <div className="w-[28rem] flex-shrink-0 h-full">
              <EmailList
                emails={filteredEmails as any}
                selectedEmail={selectedEmail as any}
                onEmailSelect={(email) => handleEmailSelect(email as DashboardEmail)}
                onToggleStar={handleToggleStar}
                isLoading={isLoadingEmails}
                activeFolder={activeFolder}
              />
            </div>

            <div className="flex-1 min-w-0 h-full">
              <EmailViewer
                email={selectedEmail as any}
                onReply={handleReply}
                onReplyAll={handleReplyAll}
                onForward={handleForward}
                onDelete={handleDeleteEmail}
                onEmailDecrypted={handleEmailDecrypted}
              />
            </div>
          </>
        ) : currentView === 'keymanager' ? (
          <div className="flex-1 overflow-hidden rounded-2xl bg-white border border-gray-200 shadow-sm flex">
            {keyManagerAuth.isLoggedIn ? (
              <KeyManagerDashboard 
                kmType={keyManagerAuth.kmType || 'KM1'}
                username={keyManagerAuth.username || 'admin'}
                onLogout={handleKeyManagerLogout} 
              />
            ) : (
              <KeyVaultLogin onLogin={handleKeyManagerLogin} />
            )}
          </div>
        ) : (
          <div className="flex-1 overflow-auto rounded-2xl bg-white border border-gray-200 shadow-sm mx-3">
            <QuantumDashboard />
          </div>
        )}
      </div>

      <NewComposeEmailModal
        isOpen={isComposeOpen}
        onClose={() => {
          setIsComposeOpen(false)
          setReplyToEmail(null)
        }}
        onSend={handleEmailSent}
        replyTo={replyToEmail as any}
        keyManagerLoggedIn={keyManagerAuth.isLoggedIn}
      />

      <SettingsPanel
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        user={headerUser}
      />
    </div>
  )
}

export default MainDashboard
