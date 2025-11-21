import { create } from 'zustand'
import toast from 'react-hot-toast'
import { apiService } from '../services/api'

const decodeHtmlEntities = (text: string) =>
  text
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")

const CSS_MEDIA_QUERY = /@[a-z\-]+[^{}]*\{[\s\S]*?\}/gi
const CSS_SELECTOR_BLOCK = /(?:^|\s)(?:[#.][\w-]+|[a-z0-9_-]+\s+[a-z0-9_.#-]+|body|html)[^{]*\{[^{}]*:[^{}]*\}/gi

const stripCssArtifacts = (text: string) =>
  text
    .replace(CSS_MEDIA_QUERY, ' ')
    .replace(CSS_SELECTOR_BLOCK, ' ')
    .replace(/\/\*[\s\S]*?\*\//g, ' ')

const sanitizeSnippet = (rawSnippet: string, fallbackHtml?: string, fallbackText?: string) => {
  const source = rawSnippet || fallbackText || fallbackHtml || ''
  if (!source) return ''

  const cleaned = stripCssArtifacts(
    source
      .replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, ' ')
      .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\r|\n/g, ' ')
  )

  return decodeHtmlEntities(cleaned)
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 220)
}

export interface Email {
  id: string
  threadId: string
  subject: string
  fromAddress?: string
  toAddress?: string
  sender?: string
  recipient?: string
  ccAddress?: string
  bccAddress?: string
  body?: string
  bodyText?: string
  bodyHtml?: string
  securityLevel: string | number
  timestamp: string
  isRead: boolean
  isStarred: boolean
  isSuspicious: boolean
  hasAttachments: boolean
  attachments?: Array<{
    id: string
    filename: string
    size: number
    mimeType: string
  }>
  labels: string[]
  snippet: string
  source?: string
}

export interface EmailFilter {
  folder: string
  securityLevel?: 1 | 2 | 3 | 4
  searchQuery?: string
  isRead?: boolean
  hasAttachments?: boolean
}

interface EmailState {
  // State
  emails: Email[]
  selectedEmailId: string | null
  currentFilter: EmailFilter
  isLoading: boolean
  isLoadingEmail: boolean
  error: string | null
  unreadCount: number
  hasMore: boolean
  pageToken?: string

  // Actions
  fetchEmails: (filter?: Partial<EmailFilter>, reset?: boolean) => Promise<void>
  fetchEmailDetails: (emailId: string) => Promise<Email | null>
  selectEmail: (emailId: string | null) => void
  markAsRead: (emailId: string) => Promise<void>
  markAsUnread: (emailId: string) => Promise<void>
  toggleStar: (emailId: string) => Promise<void>
  deleteEmail: (emailId: string) => Promise<void>
  moveToTrash: (emailId: string) => Promise<void>
  archiveEmail: (emailId: string) => Promise<void>
  refreshEmails: () => Promise<void>
  setFilter: (filter: Partial<EmailFilter>) => void
  clearError: () => void
  updateUnreadCount: () => void
}

export const useEmailStore = create<EmailState>((set, get) => ({
  // Initial state
  emails: [],
  selectedEmailId: null,
  currentFilter: { folder: 'gmail_inbox' as any },
  isLoading: false,
  isLoadingEmail: false,
  error: null,
  unreadCount: 0,
  hasMore: true,
  pageToken: undefined,

  // Fetch emails based on filter
  fetchEmails: async (filter = {}, reset = false) => {
    try {
      set({ isLoading: true, error: null })
      
      const newFilter = { ...get().currentFilter, ...filter }
      
      if (reset) {
        set({ emails: [], pageToken: undefined, hasMore: true })
      }

      const response = await apiService.getEmails({
        folder: newFilter.folder,
        securityLevel: newFilter.securityLevel,
        searchQuery: newFilter.searchQuery,
        isRead: newFilter.isRead,
        hasAttachments: newFilter.hasAttachments,
        pageToken: reset ? undefined : get().pageToken,
        maxResults: 50,
      })

      const currentEmails = reset ? [] : get().emails
      const newEmails = (response.emails || []).map((email: any) => ({
        id: email.id,
        threadId: email.threadId || '',
        subject: email.subject || '(No subject)',
        fromAddress: email.fromAddress,
        toAddress: email.toAddress,
        sender: email.sender,
        recipient: email.recipient,
        ccAddress: email.ccAddress,
        bccAddress: email.bccAddress,
        body: email.body || email.bodyText,
        bodyText: email.bodyText,
        bodyHtml: email.bodyHtml,
        securityLevel: email.securityLevel ?? 'standard',
        timestamp: email.timestamp || new Date().toISOString(),
        isRead: email.isRead ?? true,
        isStarred: email.isStarred ?? false,
        isSuspicious: email.isSuspicious ?? false,
        hasAttachments: email.hasAttachments ?? false,
        attachments: email.attachments || [],
        labels: email.labels || [],
        snippet: sanitizeSnippet(email.snippet || '', email.bodyHtml, email.bodyText || email.body),
        source: email.source || (email.id?.startsWith('gmail_') ? 'gmail' : 'qumail'),
      }))

      set({
        emails: [...currentEmails, ...newEmails],
        currentFilter: newFilter,
        isLoading: false,
        hasMore: !!response.nextPageToken,
        pageToken: response.nextPageToken,
      })

      // Update unread count
      get().updateUnreadCount()
      
    } catch (error: any) {
      console.error('Failed to fetch emails:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to fetch emails'
      
      set({
        error: errorMessage,
        isLoading: false,
      })
      
      toast.error(errorMessage)
    }
  },

  // Fetch detailed email content
  fetchEmailDetails: async (emailId: string) => {
    try {
      set({ isLoadingEmail: true, error: null })
      
      const email = await apiService.getEmailDetails(emailId)
      
      // Update the email in the list
      set(state => ({
        emails: state.emails.map(e => 
          e.id === emailId ? { ...e, ...email } : e
        ),
        isLoadingEmail: false,
      }))
      
      return email
    } catch (error: any) {
      console.error('Failed to fetch email details:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to fetch email details'
      
      set({
        error: errorMessage,
        isLoadingEmail: false,
      })
      
      toast.error(errorMessage)
      return null
    }
  },

  // Select an email
  selectEmail: (emailId: string | null) => {
    set({ selectedEmailId: emailId })
    
    // Auto-mark as read when selected
    if (emailId) {
      const email = get().emails.find(e => e.id === emailId)
      if (email && !email.isRead) {
        get().markAsRead(emailId)
      }
    }
  },

  // Mark email as read
  markAsRead: async (emailId: string) => {
    try {
      await apiService.markEmailAsRead(emailId, true)
      
      set(state => ({
        emails: state.emails.map(email =>
          email.id === emailId ? { ...email, isRead: true } : email
        ),
      }))
      
      get().updateUnreadCount()
    } catch (error: any) {
      console.error('Failed to mark email as read:', error)
      toast.error('Failed to mark email as read')
    }
  },

  // Mark email as unread
  markAsUnread: async (emailId: string) => {
    try {
      await apiService.markEmailAsRead(emailId, false)
      
      set(state => ({
        emails: state.emails.map(email =>
          email.id === emailId ? { ...email, isRead: false } : email
        ),
      }))
      
      get().updateUnreadCount()
      toast.success('Marked as unread')
    } catch (error: any) {
      console.error('Failed to mark email as unread:', error)
      toast.error('Failed to mark email as unread')
    }
  },

  // Toggle star status
  toggleStar: async (emailId: string) => {
    try {
      const email = get().emails.find(e => e.id === emailId)
      if (!email) return

      await apiService.toggleEmailStar(emailId, !email.isStarred)
      
      set(state => ({
        emails: state.emails.map(e =>
          e.id === emailId ? { ...e, isStarred: !e.isStarred } : e
        ),
      }))
      
      toast.success(email.isStarred ? 'Removed from starred' : 'Added to starred')
    } catch (error: any) {
      console.error('Failed to toggle star:', error)
      toast.error('Failed to update star status')
    }
  },

  // Delete email permanently
  deleteEmail: async (emailId: string) => {
    try {
      await apiService.deleteEmail(emailId)
      
      set(state => ({
        emails: state.emails.filter(email => email.id !== emailId),
        selectedEmailId: state.selectedEmailId === emailId ? null : state.selectedEmailId,
      }))
      
      get().updateUnreadCount()
      toast.success('Email deleted')
    } catch (error: any) {
      console.error('Failed to delete email:', error)
      toast.error('Failed to delete email')
    }
  },

  // Move to trash
  moveToTrash: async (emailId: string) => {
    try {
      await apiService.moveEmailToTrash(emailId)
      
      // Remove from current view if not in trash folder
      if (get().currentFilter.folder !== 'trash') {
        set(state => ({
          emails: state.emails.filter(email => email.id !== emailId),
          selectedEmailId: state.selectedEmailId === emailId ? null : state.selectedEmailId,
        }))
      }
      
      get().updateUnreadCount()
      toast.success('Moved to trash')
    } catch (error: any) {
      console.error('Failed to move to trash:', error)
      toast.error('Failed to move to trash')
    }
  },

  // Archive email
  archiveEmail: async (emailId: string) => {
    try {
      await apiService.archiveEmail(emailId)
      
      // Remove from inbox view
      if (get().currentFilter.folder === 'inbox') {
        set(state => ({
          emails: state.emails.filter(email => email.id !== emailId),
          selectedEmailId: state.selectedEmailId === emailId ? null : state.selectedEmailId,
        }))
      }
      
      get().updateUnreadCount()
      toast.success('Email archived')
    } catch (error: any) {
      console.error('Failed to archive email:', error)
      toast.error('Failed to archive email')
    }
  },

  // Refresh emails
  refreshEmails: async () => {
    await get().fetchEmails({}, true)
  },

  // Set filter
  setFilter: (filter: Partial<EmailFilter>) => {
    const newFilter = { ...get().currentFilter, ...filter }
    set({ currentFilter: newFilter })
    get().fetchEmails(filter, true)
  },

  // Clear error
  clearError: () => {
    set({ error: null })
  },

  // Update unread count
  updateUnreadCount: () => {
    const unreadCount = get().emails.filter(email => !email.isRead).length
    set({ unreadCount })
  },
}))