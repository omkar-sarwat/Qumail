import { create } from 'zustand'
import toast from 'react-hot-toast'
import { apiService } from '../services/api'

export interface EmailDraft {
  id?: string
  to: string
  cc?: string
  bcc?: string
  subject: string
  body: string
  isHtml: boolean
  securityLevel: 1 | 2 | 3 | 4
  attachments: File[]
  isScheduled: boolean
  scheduledDate?: Date
}

export interface ComposerState {
  // State
  isOpen: boolean
  draft: EmailDraft
  isSending: boolean
  isSavingDraft: boolean
  isUploading: boolean
  uploadProgress: number
  lastSavedAt?: Date
  recipients: Array<{
    email: string
    name?: string
    isValid: boolean
  }>
  isFullscreen: boolean
  
  // Actions
  openComposer: (draft?: Partial<EmailDraft>) => void
  closeComposer: () => void
  updateDraft: (updates: Partial<EmailDraft>) => void
  sendEmail: () => Promise<boolean>
  saveDraft: () => Promise<void>
  loadDraft: (draftId: string) => Promise<void>
  deleteDraft: (draftId: string) => Promise<void>
  addAttachment: (file: File) => Promise<void>
  removeAttachment: (fileName: string) => void
  validateRecipients: () => void
  scheduleEmail: (date: Date) => Promise<boolean>
  toggleFullscreen: () => void
  resetComposer: () => void
}

const defaultDraft: EmailDraft = {
  to: '',
  cc: '',
  bcc: '',
  subject: '',
  body: '',
  isHtml: false,
  securityLevel: 3, // Default to Post-Quantum
  attachments: [],
  isScheduled: false,
}

export const useComposerStore = create<ComposerState>((set, get) => ({
  // Initial state
  isOpen: false,
  draft: { ...defaultDraft },
  isSending: false,
  isSavingDraft: false,
  isUploading: false,
  uploadProgress: 0,
  lastSavedAt: undefined,
  recipients: [],
  isFullscreen: false,

  // Open composer
  openComposer: (draft = {}) => {
    set({
      isOpen: true,
      draft: { ...defaultDraft, ...draft },
      recipients: [],
      lastSavedAt: undefined,
    })
    
    // Validate recipients if any
    if (draft.to || draft.cc || draft.bcc) {
      get().validateRecipients()
    }
  },

  // Close composer
  closeComposer: () => {
    const { draft, isSending } = get()
    
    // Prevent closing while sending
    if (isSending) {
      toast.error('Cannot close while sending email')
      return
    }
    
    // Auto-save draft if there's content
    if (draft.subject || draft.body || draft.to) {
      get().saveDraft()
    }
    
    set({
      isOpen: false,
      isFullscreen: false,
    })
  },

  // Update draft
  updateDraft: (updates: Partial<EmailDraft>) => {
    set(state => ({
      draft: { ...state.draft, ...updates },
    }))
    
    // Validate recipients if email fields changed
    if (updates.to !== undefined || updates.cc !== undefined || updates.bcc !== undefined) {
      get().validateRecipients()
    }
    
    // Auto-save after a delay (debounced in real implementation)
    const { draft } = get()
    if (draft.subject || draft.body || draft.to) {
      setTimeout(() => {
        get().saveDraft()
      }, 2000)
    }
  },

  // Send email
  sendEmail: async () => {
    try {
      const { draft, recipients } = get()
      
      // Validation
      if (!draft.to.trim()) {
        toast.error('Please enter a recipient email address')
        return false
      }
      
      if (!draft.subject.trim()) {
        toast.error('Please enter a subject')
        return false
      }
      
      if (!draft.body.trim()) {
        toast.error('Please enter email content')
        return false
      }
      
      // Check for invalid recipients
      const invalidRecipients = recipients.filter(r => !r.isValid)
      if (invalidRecipients.length > 0) {
        toast.error('Please fix invalid email addresses')
        return false
      }
      
      set({ isSending: true })
      
      // Prepare email data
      const emailData = {
        to: draft.to,
        cc: draft.cc || undefined,
        bcc: draft.bcc || undefined,
        subject: draft.subject,
        body: draft.body,
        isHtml: draft.isHtml,
        securityLevel: draft.securityLevel,
        attachments: draft.attachments,
        isScheduled: draft.isScheduled,
        scheduledDate: draft.scheduledDate ? draft.scheduledDate.toISOString() : undefined,
      }
      
      if (draft.isScheduled && draft.scheduledDate) {
        const emailDataWithSchedule = {
          ...emailData,
          scheduledDate: draft.scheduledDate.toISOString(),
        }
        await apiService.scheduleEmail(emailDataWithSchedule)
        toast.success('Email scheduled successfully')
      } else {
        await apiService.sendEmail(emailData)
        toast.success('Email sent successfully')
      }
      
      // Clear draft and close composer
      set({
        isSending: false,
        isOpen: false,
        isFullscreen: false,
        draft: { ...defaultDraft },
        recipients: [],
        lastSavedAt: undefined,
      })
      
      // Delete draft if it was saved
      if (draft.id) {
        await apiService.deleteDraft(draft.id)
      }
      
      return true
      
    } catch (error: any) {
      console.error('Failed to send email:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to send email'
      
      set({ isSending: false })
      toast.error(errorMessage)
      return false
    }
  },

  // Save draft
  saveDraft: async () => {
    try {
      const { draft, isSavingDraft } = get()
      
      // Prevent multiple saves
      if (isSavingDraft) return
      
      // Only save if there's meaningful content
      if (!draft.subject && !draft.body && !draft.to) return
      
      set({ isSavingDraft: true })
      
      const draftData = {
        ...draft,
        scheduledDate: draft.scheduledDate ? draft.scheduledDate.toISOString() : undefined,
      }
      
      let savedDraft
      if (draft.id) {
        savedDraft = await apiService.updateDraft(draft.id, draftData)
      } else {
        savedDraft = await apiService.saveDraft(draftData)
      }
      
      set({
        draft: { ...draft, id: savedDraft.id },
        isSavingDraft: false,
        lastSavedAt: new Date(),
      })
      
    } catch (error: any) {
      console.error('Failed to save draft:', error)
      set({ isSavingDraft: false })
      
      // Don't show error toast for auto-saves to avoid spam
      if (!error.isAutoSave) {
        toast.error('Failed to save draft')
      }
    }
  },

  // Load draft
  loadDraft: async (draftId: string) => {
    try {
      const draft = await apiService.getDraft(draftId)
      
      set({
        isOpen: true,
        draft: {
          ...draft,
          scheduledDate: draft.scheduledDate ? new Date(draft.scheduledDate) : undefined,
        },
        recipients: [],
      })
      
      get().validateRecipients()
      
    } catch (error: any) {
      console.error('Failed to load draft:', error)
      toast.error('Failed to load draft')
    }
  },

  // Delete draft
  deleteDraft: async (draftId: string) => {
    try {
      await apiService.deleteDraft(draftId)
      
      // If the current draft is being deleted, reset composer
      if (get().draft.id === draftId) {
        set({
          draft: { ...defaultDraft },
          recipients: [],
          lastSavedAt: undefined,
        })
      }
      
      toast.success('Draft deleted')
      
    } catch (error: any) {
      console.error('Failed to delete draft:', error)
      toast.error('Failed to delete draft')
    }
  },

  // Add attachment
  addAttachment: async (file: File) => {
    try {
      // Validate file size (10MB limit)
      const maxSize = 10 * 1024 * 1024
      if (file.size > maxSize) {
        toast.error('File size must be less than 10MB')
        return
      }
      
      // Validate file type
      const allowedTypes = [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
      ]
      
      if (!allowedTypes.includes(file.type)) {
        toast.error('File type not supported')
        return
      }
      
      set({ isUploading: true, uploadProgress: 0 })
      
      try {
        // Add to attachments immediately (for local files)
        set(state => ({
          draft: {
            ...state.draft,
            attachments: [...state.draft.attachments, file]
          },
          isUploading: false,
          uploadProgress: 100,
        }))

        // Reset progress after brief delay
        setTimeout(() => {
          set({ uploadProgress: 0 })
        }, 1000)

        toast.success(`Added ${file.name}`)
      } catch (error) {
        set({ isUploading: false, uploadProgress: 0 })
        toast.error('Failed to add attachment')
      }
      
    } catch (error: any) {
      console.error('Failed to add attachment:', error)
      set({ isUploading: false, uploadProgress: 0 })
      toast.error('Failed to add attachment')
    }
  },

  // Remove attachment
  removeAttachment: (fileName: string) => {
    set(state => ({
      draft: {
        ...state.draft,
        attachments: state.draft.attachments.filter(file => file.name !== fileName)
      }
    }))
    
    toast.success('Attachment removed')
  },

  // Validate recipients
  validateRecipients: () => {
    const { draft } = get()
    const allEmails = [
      ...draft.to.split(',').filter(e => e.trim()),
      ...draft.cc?.split(',').filter(e => e.trim()) || [],
      ...draft.bcc?.split(',').filter(e => e.trim()) || [],
    ]
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    
    const recipients = allEmails.map(email => {
      const trimmedEmail = email.trim()
      return {
        email: trimmedEmail,
        isValid: emailRegex.test(trimmedEmail)
      }
    })
    
    set({ recipients })
  },

  // Schedule email
  scheduleEmail: async (date: Date) => {
    const now = new Date()
    
    if (date <= now) {
      toast.error('Scheduled time must be in the future')
      return false
    }
    
    set(state => ({
      draft: {
        ...state.draft,
        isScheduled: true,
        scheduledDate: date,
      }
    }))
    
    return get().sendEmail()
  },

  // Toggle fullscreen
  toggleFullscreen: () => {
    set(state => ({
      isFullscreen: !state.isFullscreen
    }))
  },

  // Reset composer
  resetComposer: () => {
    set({
      isOpen: false,
      draft: { ...defaultDraft },
      isSending: false,
      isSavingDraft: false,
      isUploading: false,
      uploadProgress: 0,
      lastSavedAt: undefined,
      recipients: [],
      isFullscreen: false,
    })
  },
}))