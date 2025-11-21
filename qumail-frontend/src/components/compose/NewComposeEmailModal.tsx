import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import { 
  X, 
  Bold, 
  Italic, 
  Underline as UnderlineIcon, 
  Strikethrough,
  List,
  ListOrdered,
  Link as LinkIcon,
  Code,
  Paperclip,
  Send,
  ChevronDown,
  Lock,
  Loader2,
  Check,
  FileText,
  Trash2,
  Clock
} from 'lucide-react'

// ============================================
// INTERFACES & TYPES
// ============================================

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

interface NewComposeEmailModalProps {
  isOpen: boolean
  onClose: () => void
  onSend: (summary: QuantumSendSummary) => void
  replyTo?: Email | null
}

export interface QuantumSendSummary {
  success: boolean
  message: string
  flowId: string
  gmailMessageId?: string
  gmailThreadId?: string
  encryptionMethod: string
  securityLevel: number
  emailId?: number
  emailUuid?: string
  entropy?: number
  keyId?: string
  encryptedSize?: number
  timestamp?: string
  sentViaGmail: boolean
}

interface Contact {
  email: string
  name: string
  avatar?: string
}

interface Attachment {
  file: File
  id: string
  progress: number
}

interface Draft {
  id: string
  draftId: string
  to: string
  recipient: string
  subject: string
  body: string
  securityLevel: 1 | 2 | 3 | 4
  security_level: 1 | 2 | 3 | 4
  cc?: string
  bcc?: string
  created_at: string
  updated_at: string
}

// ============================================
// SECURITY LEVEL CONFIGURATION
// ============================================

const SECURITY_LEVELS = [
  {
    value: 1,
    name: 'Quantum Secure (Level 1)',
    shortName: 'Level 1',
    description: 'One Time Pad with Quantum Keys - Maximum Security',
    color: 'purple',
    icon: Lock,
    gradient: 'from-purple-500 to-purple-700'
  },
  {
    value: 2,
    name: 'Quantum-Aided AES (Level 2)',
    shortName: 'Level 2',
    description: 'AES encryption with quantum key enhancement',
    color: 'blue',
    icon: Lock,
    gradient: 'from-blue-500 to-blue-700'
  },
  {
    value: 3,
    name: 'Post-Quantum (Level 3)',
    shortName: 'Level 3',
    description: 'Future-proof encryption for post-quantum era',
    color: 'green',
    icon: Lock,
    gradient: 'from-green-500 to-green-700'
  },
  {
    value: 4,
    name: 'Standard (Level 4)',
    shortName: 'Level 4',
    description: 'Regular encryption without quantum enhancement',
    color: 'gray',
    icon: Lock,
    gradient: 'from-gray-500 to-gray-600'
  }
] as const

// ============================================
// MAIN COMPONENT
// ============================================

export const NewComposeEmailModal: React.FC<NewComposeEmailModalProps> = ({
  isOpen,
  onClose,
  onSend,
  replyTo
}) => {
  // ============================================
  // STATE MANAGEMENT
  // ============================================
  
  const [to, setTo] = useState('')
  const [cc, setCc] = useState('')
  const [bcc, setBcc] = useState('')
  const [subject, setSubject] = useState('')
  const [securityLevel, setSecurityLevel] = useState<1 | 2 | 3 | 4>(1)
  const [showCcBcc, setShowCcBcc] = useState(false)
  const [showSecurityDropdown, setShowSecurityDropdown] = useState(false)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [isSending, setIsSending] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showContacts, setShowContacts] = useState(false)
  const [encryptionStatus, setEncryptionStatus] = useState('')
  const [draftSaved, setDraftSaved] = useState(false)
  const [showLinkDialog, setShowLinkDialog] = useState(false)
  const [linkUrl, setLinkUrl] = useState('')
  const [showDrafts, setShowDrafts] = useState(false)
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [loadingDrafts, setLoadingDrafts] = useState(false)
  const [currentDraftId, setCurrentDraftId] = useState<string | null>(null)

  // ============================================
  // REFS
  // ============================================
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const securityDropdownRef = useRef<HTMLDivElement>(null)
  const contactsDropdownRef = useRef<HTMLDivElement>(null)

  // ============================================
  // TIPTAP EDITOR CONFIGURATION
  // ============================================
  
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3]
        },
        bulletList: {
          keepMarks: true,
          keepAttributes: false
        },
        orderedList: {
          keepMarks: true,
          keepAttributes: false
        }
      }),
      Underline,
      Link.configure({
        openOnClick: false,
        linkOnPaste: true,
        HTMLAttributes: {
          class: 'text-blue-600 underline cursor-pointer hover:text-blue-800'
        }
      })
    ],
    content: '',
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[300px] px-4 py-3 text-gray-900 dark:text-white'
      }
    },
    onUpdate: () => {
      // Auto-save draft logic could go here
      setDraftSaved(false)
    }
  })

  // ============================================
  // CONTACTS STATE FOR AUTOCOMPLETE
  // ============================================
  
  const [contacts, setContacts] = useState<Contact[]>([
    { email: 'alice@example.com', name: 'Alice Johnson' },
    { email: 'bob@example.com', name: 'Bob Smith' },
    { email: 'carol@example.com', name: 'Carol Williams' },
    { email: 'david@example.com', name: 'David Brown' },
    { email: 'eve@example.com', name: 'Eve Martinez' }
  ])

  // ============================================
  // EFFECTS
  // ============================================
  
  // Handle reply-to email population
  useEffect(() => {
    if (replyTo && editor) {
      const senderEmail = replyTo.sender_email || replyTo.from_email || replyTo.from || ''
      setTo(senderEmail)
      
      const subjectText = replyTo.subject || '(No Subject)'
      setSubject(subjectText.startsWith('Re: ') ? subjectText : `Re: ${subjectText}`)
      
      const senderName = replyTo.sender_name || replyTo.from_name || 
        (replyTo.from && replyTo.from.includes('<') ? 
          replyTo.from.split('<')[0].trim().replace(/"/g, '') : 
          replyTo.from?.split('@')[0]) || 'Unknown Sender'
      
      const bodyContent = replyTo.html_body || replyTo.body || replyTo.plain_body || '(No content)'
      
      const replyContent = `
        <br><br>
        <div style="border-left: 3px solid #cbd5e1; padding-left: 12px; margin-top: 16px; color: #64748b;">
          <p style="margin: 0; font-weight: 600;">--- Original Message ---</p>
          <p style="margin: 4px 0 0 0;"><strong>From:</strong> ${senderName} &lt;${senderEmail}&gt;</p>
          <p style="margin: 4px 0 0 0;"><strong>Subject:</strong> ${replyTo.subject || '(No Subject)'}</p>
          <p style="margin: 4px 0 0 0;"><strong>Date:</strong> ${new Date(replyTo.timestamp).toLocaleString()}</p>
          <br>
          ${bodyContent}
        </div>
      `
      
      editor.commands.setContent(replyContent)
      setSecurityLevel(replyTo.securityLevel || 4)
    } else if (!replyTo && editor) {
      resetForm()
    }
  }, [replyTo, editor])

  // Focus editor when modal opens
  useEffect(() => {
    if (isOpen && editor) {
      setTimeout(() => {
        editor.commands.focus('start')
      }, 100)
    }
  }, [isOpen, editor])

  // Handle click outside for dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (securityDropdownRef.current && !securityDropdownRef.current.contains(event.target as Node)) {
        setShowSecurityDropdown(false)
      }
      if (contactsDropdownRef.current && !contactsDropdownRef.current.contains(event.target as Node)) {
        setShowContacts(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Auto-save draft every 30 seconds
  useEffect(() => {
    if (!isOpen) return

    const saveDraft = () => {
      if (to || subject || editor?.getText()) {
        // Simulate draft save
        setDraftSaved(true)
        setTimeout(() => setDraftSaved(false), 2000)
      }
    }

    const interval = setInterval(saveDraft, 30000)
    return () => clearInterval(interval)
  }, [isOpen, to, subject, editor])

  // ============================================
  // HELPER FUNCTIONS
  // ============================================
  
  const parseRecipientList = (value: string): string[] =>
    value
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0)

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getCurrentSecurityLevel = () => {
    return SECURITY_LEVELS.find(level => level.value === securityLevel) || SECURITY_LEVELS[0]
  }

  const resetForm = () => {
    setTo('')
    setCc('')
    setBcc('')
    setSubject('')
    setSecurityLevel(4)
    setAttachments([])
    setShowCcBcc(false)
    setEncryptionStatus('')
    setDraftSaved(false)
    editor?.commands.setContent('')
  }

  // ============================================
  // EDITOR TOOLBAR FUNCTIONS
  // ============================================
  
  const toggleBold = () => editor?.chain().focus().toggleBold().run()
  const toggleItalic = () => editor?.chain().focus().toggleItalic().run()
  const toggleUnderline = () => editor?.chain().focus().toggleUnderline().run()
  const toggleStrike = () => editor?.chain().focus().toggleStrike().run()
  const toggleBulletList = () => editor?.chain().focus().toggleBulletList().run()
  const toggleOrderedList = () => editor?.chain().focus().toggleOrderedList().run()
  const toggleCodeBlock = () => editor?.chain().focus().toggleCodeBlock().run()

  const setLink = () => {
    if (!linkUrl) {
      editor?.chain().focus().unsetLink().run()
      return
    }

    const url = linkUrl.startsWith('http') ? linkUrl : `https://${linkUrl}`
    editor?.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    setShowLinkDialog(false)
    setLinkUrl('')
  }

  const insertLink = () => {
    const previousUrl = editor?.getAttributes('link').href
    setLinkUrl(previousUrl || '')
    setShowLinkDialog(true)
  }

  // ============================================
  // FILE HANDLING
  // ============================================
  
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    const newAttachments = files.map(file => ({
      file,
      id: Math.random().toString(36).substring(7),
      progress: 100 // Simulate instant upload
    }))
    setAttachments(prev => [...prev, ...newAttachments])
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id))
  }

  // ============================================
  // CONTACT SELECTION
  // ============================================
  
  const selectContact = (contact: Contact) => {
    setTo(contact.email)
    setShowContacts(false)
  }

  const addEmailToContacts = (email: string) => {
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) return

    // Check if email already exists
    const exists = contacts.some(c => c.email.toLowerCase() === email.toLowerCase())
    if (exists) return

    // Extract name from email (part before @)
    const name = email.split('@')[0].split('.').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')

    // Add to top of contacts list
    setContacts(prev => [{ email, name }, ...prev])
  }

  const getContactInitials = (name: string): string => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2)
  }

  const getContactColor = (email: string): string => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-purple-500 to-purple-600',
      'from-pink-500 to-pink-600',
      'from-green-500 to-green-600',
      'from-yellow-500 to-yellow-600',
      'from-red-500 to-red-600'
    ]
    const index = email.charCodeAt(0) % colors.length
    return colors[index]
  }

  // ============================================
  // EMAIL SENDING
  // ============================================
  
  const fetchDrafts = async () => {
    const token = localStorage.getItem('authToken')
    if (!token) {
      console.error('❌ No auth token found')
      return
    }

    console.log('🔍 Fetching drafts from backend...')
    setLoadingDrafts(true)
    try {
      const response = await fetch('http://localhost:8000/api/v1/emails/drafts', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      console.log('📡 Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('✅ Drafts fetched from API:', data)
        console.log('   Is array?', Array.isArray(data))
        console.log('   Length:', data?.length)
        
        // Normalize response into an array
        let draftsArray: Draft[] = []
        if (Array.isArray(data)) {
          draftsArray = data as Draft[]
        } else if (data && typeof data === 'object') {
          if (Array.isArray((data as any).drafts)) {
            draftsArray = (data as any).drafts as Draft[]
          } else if ((data as any).id || (data as any)._id) {
            draftsArray = [{
              id: (data as any).id || (data as any)._id,
              draftId: (data as any).draftId || (data as any).id || (data as any)._id,
              to: (data as any).to || (data as any).recipient || '',
              recipient: (data as any).recipient || (data as any).to || '',
              subject: (data as any).subject || '',
              body: (data as any).body || '',
              securityLevel: (data as any).securityLevel || (data as any).security_level || 2,
              security_level: (data as any).securityLevel || (data as any).security_level || 2,
              cc: (data as any).cc,
              bcc: (data as any).bcc,
              created_at: (data as any).created_at || new Date().toISOString(),
              updated_at: (data as any).updated_at || new Date().toISOString()
            }]
          }
        }
        
        draftsArray = draftsArray.map(draft => ({
          ...draft,
          id: draft.id || (draft as any)._id || draft.draftId,
          draftId: draft.draftId || draft.id || (draft as any)._id,
          to: draft.to || draft.recipient || '',
          recipient: draft.recipient || draft.to || '',
          securityLevel: draft.securityLevel || draft.security_level || 2,
          security_level: draft.securityLevel || draft.security_level || 2,
          created_at: draft.created_at || new Date().toISOString(),
          updated_at: draft.updated_at || draft.created_at || new Date().toISOString()
        }))
        console.log('   Setting drafts state with:', draftsArray.length, 'items')
        setDrafts(draftsArray)
      } else {
        const errorText = await response.text()
        console.error('❌ Failed to fetch drafts, status:', response.status, 'Error:', errorText)
        setDrafts([])
      }
    } catch (error) {
      console.error('❌ Error fetching drafts:', error)
      setDrafts([])
    } finally {
      setLoadingDrafts(false)
      console.log('✅ Fetch drafts complete')
    }
  }

  const loadDraft = (draft: Draft) => {
    setTo(draft.to || draft.recipient || '')
    setCc(draft.cc || '')
    setBcc(draft.bcc || '')
    setSubject(draft.subject || '')
    setSecurityLevel(draft.securityLevel || draft.security_level || 4)
    if (editor && draft.body) {
      editor.commands.setContent(draft.body)
    }
    setCurrentDraftId(draft.id || draft.draftId)
    setShowDrafts(false)
    toast.success('Draft loaded successfully!')
  }

  const deleteDraft = async (draftId: string) => {
    const token = localStorage.getItem('authToken')
    if (!token) return

    try {
      const response = await fetch(`http://localhost:8000/api/v1/emails/drafts/${draftId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('Draft deleted!')
        fetchDrafts() // Refresh the list
      }
    } catch (error) {
      console.error('Error deleting draft:', error)
      toast.error('Failed to delete draft')
    }
  }

  const handleSaveDraft = async () => {
    const token = localStorage.getItem('authToken')
    if (!token) {
      toast.error('Authentication required. Please sign in again.')
      return
    }

    setIsSaving(true)

    try {
      const bodyContent = editor?.getHTML() || ''

      const formData = new FormData()
      if (currentDraftId) formData.append('id', currentDraftId)
      formData.append('to', to || '')
      formData.append('subject', subject || '')
      formData.append('body', bodyContent)
      formData.append('securityLevel', securityLevel.toString())
      if (cc) formData.append('cc', cc)
      if (bcc) formData.append('bcc', bcc)

      const response = await fetch('http://localhost:8000/api/v1/emails/drafts', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save draft')
      }

      const result = await response.json()
      console.log('Draft saved:', result)
      
      if (!currentDraftId && result.draftId) {
        setCurrentDraftId(result.draftId)
      }
      
      setDraftSaved(true)
      toast.success('Draft saved successfully!')
      
      setTimeout(() => setDraftSaved(false), 3000)
      
      // Refresh drafts list if panel is open
      if (showDrafts) {
        fetchDrafts()
      }

    } catch (error: any) {
      console.error('Error saving draft:', error)
      toast.error(error.message || 'Failed to save draft')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSend = async () => {
    if (!to || !subject || !editor?.getText().trim()) {
      toast.error('Please fill in To, Subject, and Message body before sending.')
      return
    }

    const token = localStorage.getItem('authToken')
    if (!token) {
      toast.error('Authentication required. Please sign in again.')
      return
    }

    setIsSending(true)

    let finalSecurityLevel = securityLevel

    try {
      // Check quantum key availability for Level 1
      if (finalSecurityLevel === 1) {
        setEncryptionStatus('Checking quantum key availability...')
        try {
          const keysResponse = await fetch('http://localhost:8000/api/v1/quantum/keys/available', {
            headers: {
              Authorization: `Bearer ${token}`
            }
          })

          if (keysResponse.ok) {
            const keysData = await keysResponse.json()
            if (!keysData.available || keysData.count === 0) {
              setEncryptionStatus('No quantum keys available. Generating new keys...')

              const exchangeResponse = await fetch('http://localhost:8000/api/v1/quantum/key/exchange', {
                method: 'POST',
                headers: {
                  Authorization: `Bearer ${token}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  sender_kme_id: 1,
                  recipient_kme_id: 2
                })
              })

              if (!exchangeResponse.ok) {
                throw new Error('Failed to generate new quantum keys')
              }
            }
          }
        } catch (keyError) {
          console.error('Error checking quantum keys:', keyError)
          setEncryptionStatus('Quantum key error. Falling back to Level 2 (Quantum AES)...')
          toast.error('Quantum keys unavailable. Falling back to Level 2 (Quantum AES).')
          finalSecurityLevel = 2
          setSecurityLevel(2)
        }
      }

      const currentLevel = SECURITY_LEVELS.find(l => l.value === finalSecurityLevel)
      setEncryptionStatus(`Encrypting with ${currentLevel?.name}...`)

      const bodyContent = editor.getHTML()

      const payload: Record<string, any> = {
        to,
        subject,
        body: bodyContent,
        security_level: finalSecurityLevel,
        type: 'quantum'
      }

      const ccList = parseRecipientList(cc)
      const bccList = parseRecipientList(bcc)
      if (ccList.length > 0) payload.cc = ccList
      if (bccList.length > 0) payload.bcc = bccList

      // Convert attachments to base64 for JSON payload
      if (attachments.length > 0) {
        setEncryptionStatus(`Processing ${attachments.length} attachment(s)...`)
        const attachmentPromises = attachments.map(async (attachment) => {
          return new Promise<any>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => {
              const base64 = reader.result as string
              resolve({
                filename: attachment.file.name,
                content: base64.split(',')[1], // Remove data:mime;base64, prefix
                mime_type: attachment.file.type,
                size: attachment.file.size
              })
            }
            reader.onerror = reject
            reader.readAsDataURL(attachment.file)
          })
        })

        payload.attachments = await Promise.all(attachmentPromises)
      }

      setEncryptionStatus('Sending encrypted email via Gmail...')
      const response = await fetch('http://localhost:8000/api/v1/emails/send/quantum', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const raw = await response.text()
      let result: any = {}
      if (raw) {
        try {
          result = JSON.parse(raw)
        } catch (parseError) {
          console.warn('Failed to parse response JSON:', parseError)
        }
      }

      if (!response.ok || result.success === false) {
        const message = result.detail || result.message || raw || 'Failed to send encrypted email'
        throw new Error(message)
      }

      const summary: QuantumSendSummary = {
        success: true,
        message: result.message || 'Quantum email sent successfully',
        flowId: result.flowId || result.flow_id || result.flowID || 'unknown-flow',
        gmailMessageId: result.gmailMessageId || result.gmail_message_id,
        gmailThreadId: result.gmailThreadId || result.gmail_thread_id,
        encryptionMethod: result.encryptionMethod || result.encryption_method || currentLevel?.name || 'Unknown',
        securityLevel: result.securityLevel || result.security_level || finalSecurityLevel,
        emailId: result.emailId ?? result.email_id,
        emailUuid: result.emailUuid || result.email_uuid,
        entropy: result.entropy,
        keyId: result.keyId || result.key_id,
        encryptedSize: result.encryptedSize ?? result.encrypted_size,
        timestamp: result.timestamp,
        sentViaGmail: result.sent_via_gmail !== undefined ? result.sent_via_gmail : true
      }

      console.info('Quantum email sent successfully', summary)

      setEncryptionStatus(`Successfully sent with ${summary.encryptionMethod}!`)

      toast.success(`✉️ Email sent with ${currentLevel?.name}`, {
        duration: 4000,
        style: {
          background: '#10b981',
          color: 'white'
        }
      })

      resetForm()
      setIsSending(false)
      setEncryptionStatus('')
      onSend(summary)
    } catch (error: any) {
      console.error('Error sending email:', error)
      const message = error?.message || 'Network or server error'
      setEncryptionStatus(`Failed: ${message}`)
      toast.error(`Failed to send email: ${message}`, {
        duration: 5000,
        style: {
          background: '#ef4444',
          color: 'white'
        }
      })
      setIsSending(false)
    }
  }

  // ============================================
  // RENDER
  // ============================================
  
  if (!editor) return null

  const currentSecurity = getCurrentSecurityLevel()

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 z-50"
            style={{ willChange: 'opacity' }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ willChange: 'opacity, transform', transform: 'translateZ(0)' }}
          >
            <div className="w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
              
              {/* ============================================ */}
              {/* HEADER */}
              {/* ============================================ */}
              
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  New Message
                </h2>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setShowDrafts(!showDrafts)
                      if (!showDrafts) fetchDrafts()
                    }}
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
                    disabled={isSending}
                    title="View saved drafts"
                  >
                    <FileText className="w-4 h-4" />
                    <span className="text-sm font-medium">Drafts</span>
                  </button>
                  
                  <button
                    onClick={onClose}
                    className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                    disabled={isSending}
                  >
                    <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  </button>
                </div>
              </div>

              {/* ============================================ */}
              {/* RECIPIENTS SECTION */}
              {/* ============================================ */}
              
              <div className="border-b border-gray-200 dark:border-gray-700">
                {/* To Field */}
                <div className="flex items-center px-6 py-3 border-b border-gray-100 dark:border-gray-800">
                  <label className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300">
                    To:
                  </label>
                  <div className="flex-1 relative" ref={contactsDropdownRef}>
                    <input
                      type="email"
                      value={to}
                      onChange={(e) => {
                        const value = e.target.value
                        setTo(value)
                        // Add to contacts when user finishes typing (has @ and .)
                        if (value.includes('@') && value.includes('.')) {
                          addEmailToContacts(value)
                        }
                      }}
                      onFocus={() => setShowContacts(true)}
                      onBlur={() => {
                        // Add on blur if valid
                        if (to) addEmailToContacts(to)
                      }}
                      placeholder="Recipients (e.g., alice@example.com, bob@example.com)"
                      className="w-full px-3 py-2 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none"
                      disabled={isSending}
                    />
                    
                    {/* Contacts Dropdown */}
                    <AnimatePresence>
                      {showContacts && contacts.length > 0 && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-10 max-h-64 overflow-y-auto"
                        >
                          {contacts.map((contact, index) => (
                            <button
                              key={index}
                              onClick={() => selectContact(contact)}
                              className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3 transition-colors border-b border-gray-100 dark:border-gray-800 last:border-b-0"
                            >
                              <div className={`w-10 h-10 bg-gradient-to-br ${getContactColor(contact.email)} rounded-full flex items-center justify-center flex-shrink-0`}>
                                <span className="text-white text-sm font-semibold">
                                  {getContactInitials(contact.name)}
                                </span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                  {contact.name}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                  {contact.email}
                                </p>
                              </div>
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  
                  <button
                    onClick={() => setShowCcBcc(!showCcBcc)}
                    className="ml-2 px-3 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                    disabled={isSending}
                  >
                    Cc/Bcc
                  </button>
                </div>

                {/* Cc/Bcc Fields */}
                <AnimatePresence>
                  {showCcBcc && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="flex items-center px-6 py-3 border-b border-gray-100 dark:border-gray-800">
                        <label className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300">
                          Cc:
                        </label>
                        <input
                          type="email"
                          value={cc}
                          onChange={(e) => setCc(e.target.value)}
                          placeholder="Carbon copy recipients"
                          className="flex-1 px-3 py-2 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none"
                          disabled={isSending}
                        />
                      </div>
                      
                      <div className="flex items-center px-6 py-3 border-b border-gray-100 dark:border-gray-800">
                        <label className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300">
                          Bcc:
                        </label>
                        <input
                          type="email"
                          value={bcc}
                          onChange={(e) => setBcc(e.target.value)}
                          placeholder="Blind carbon copy recipients"
                          className="flex-1 px-3 py-2 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none"
                          disabled={isSending}
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Subject Field */}
                <div className="flex items-center px-6 py-3">
                  <label className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Subject:
                  </label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Enter subject"
                    className="flex-1 px-3 py-2 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none"
                    disabled={isSending}
                  />
                </div>
              </div>

              {/* ============================================ */}
              {/* FORMATTING TOOLBAR */}
              {/* ============================================ */}
              
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-center space-x-1">
                  {/* Bold */}
                  <button
                    onClick={toggleBold}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('bold') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Bold (Ctrl+B)"
                  >
                    <Bold className="w-4 h-4" />
                  </button>

                  {/* Italic */}
                  <button
                    onClick={toggleItalic}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('italic') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Italic (Ctrl+I)"
                  >
                    <Italic className="w-4 h-4" />
                  </button>

                  {/* Underline */}
                  <button
                    onClick={toggleUnderline}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('underline') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Underline (Ctrl+U)"
                  >
                    <UnderlineIcon className="w-4 h-4" />
                  </button>

                  {/* Strikethrough */}
                  <button
                    onClick={toggleStrike}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('strike') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Strikethrough"
                  >
                    <Strikethrough className="w-4 h-4" />
                  </button>

                  <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

                  {/* Bullet List */}
                  <button
                    onClick={toggleBulletList}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('bulletList') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Bullet List"
                  >
                    <List className="w-4 h-4" />
                  </button>

                  {/* Numbered List */}
                  <button
                    onClick={toggleOrderedList}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('orderedList') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Numbered List"
                  >
                    <ListOrdered className="w-4 h-4" />
                  </button>

                  <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

                  {/* Link */}
                  <button
                    onClick={insertLink}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('link') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Insert Link"
                  >
                    <LinkIcon className="w-4 h-4" />
                  </button>

                  {/* Code Block */}
                  <button
                    onClick={toggleCodeBlock}
                    disabled={isSending}
                    className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
                      editor.isActive('codeBlock') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : 'text-gray-700 dark:text-gray-300'
                    }`}
                    title="Code Block"
                  >
                    <Code className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* ============================================ */}
              {/* EDITOR CONTENT */}
              {/* ============================================ */}
              
              <div className="flex-1 overflow-y-auto">
                <EditorContent 
                  editor={editor} 
                  className="h-full"
                  disabled={isSending}
                />
              </div>

              {/* ============================================ */}
              {/* ATTACHMENTS */}
              {/* ============================================ */}
              
              <AnimatePresence>
                {attachments.length > 0 && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 overflow-hidden"
                  >
                    <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      Attachments ({attachments.length})
                    </h4>
                    <div className="space-y-2">
                      {attachments.map((attachment) => (
                        <div
                          key={attachment.id}
                          className="flex items-center justify-between p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg"
                        >
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <Paperclip className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {attachment.file.name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {formatFileSize(attachment.file.size)}
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => removeAttachment(attachment.id)}
                            disabled={isSending}
                            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ============================================ */}
              {/* FOOTER */}
              {/* ============================================ */}
              
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
                
                {/* Left Actions */}
                <div className="flex items-center space-x-3">
                  {/* Security Dropdown */}
                  <div className="relative" ref={securityDropdownRef}>
                    <button
                      onClick={() => setShowSecurityDropdown(!showSecurityDropdown)}
                      disabled={isSending}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all bg-gradient-to-r ${currentSecurity.gradient} text-white hover:shadow-lg`}
                    >
                      <Lock className="w-4 h-4" />
                      <span>{currentSecurity.shortName}</span>
                      <ChevronDown className={`w-4 h-4 transition-transform ${showSecurityDropdown ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                      {showSecurityDropdown && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="absolute bottom-full left-0 mb-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl overflow-hidden z-10"
                        >
                          {SECURITY_LEVELS.map((level) => (
                            <button
                              key={level.value}
                              onClick={() => {
                                setSecurityLevel(level.value)
                                setShowSecurityDropdown(false)
                              }}
                              className={`w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border-b border-gray-100 dark:border-gray-800 last:border-b-0 ${
                                securityLevel === level.value ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                              }`}
                            >
                              <div className="flex items-start space-x-3">
                                <div className={`p-2 rounded-lg bg-gradient-to-br ${level.gradient} flex-shrink-0`}>
                                  <level.icon className="w-4 h-4 text-white" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                    {level.name}
                                  </p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {level.description}
                                  </p>
                                </div>
                                {securityLevel === level.value && (
                                  <Check className="w-5 h-5 text-blue-600 flex-shrink-0" />
                                )}
                              </div>
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Attach Files */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isSending}
                    className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
                    title="Attach Files"
                  >
                    <Paperclip className="w-5 h-5" />
                  </button>

                  {/* Draft Status */}
                  <AnimatePresence>
                    {draftSaved && (
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        className="flex items-center space-x-2 text-xs text-green-600 dark:text-green-400"
                      >
                        <Check className="w-4 h-4" />
                        <span>Draft saved a moment ago</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Right Actions */}
                <div className="flex items-center space-x-3">
                  {/* Encryption Status */}
                  {encryptionStatus && (
                    <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>{encryptionStatus}</span>
                    </div>
                  )}

                  {/* Save Draft Button */}
                  <button
                    onClick={handleSaveDraft}
                    disabled={isSaving || (!to && !subject && !editor?.getText().trim())}
                    className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
                      isSaving || (!to && !subject && !editor?.getText().trim())
                        ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600'
                    }`}
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Save Draft</span>
                      </>
                    )}
                  </button>

                  {/* Send Button */}
                  <button
                    onClick={handleSend}
                    disabled={isSending || !to || !subject || !editor.getText().trim()}
                    className={`flex items-center space-x-2 px-6 py-2.5 rounded-lg font-semibold text-sm transition-all ${
                      isSending || !to || !subject || !editor.getText().trim()
                        ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl'
                    }`}
                  >
                    {isSending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Sending...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        <span>Send</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* ============================================ */}
          {/* DRAFTS PANEL */}
          {/* ============================================ */}
          
          <AnimatePresence>
            {showDrafts && (
              <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="fixed right-0 top-0 bottom-0 w-96 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 shadow-2xl z-[60] flex flex-col"
              >
                {/* Drafts Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Saved Drafts
                  </h3>
                  <button
                    onClick={() => setShowDrafts(false)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                  </button>
                </div>

                {/* Drafts List */}
                <div className="flex-1 overflow-y-auto">
                  {loadingDrafts ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    </div>
                  ) : drafts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                      <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No saved drafts yet
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        Click "Save Draft" to save your work
                      </p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-200 dark:divide-gray-800">
                      {drafts.map((draft) => (
                        <div
                          key={draft.id}
                          className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <button
                              onClick={() => loadDraft(draft)}
                              className="flex-1 text-left"
                            >
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                  {draft.subject || '(No Subject)'}
                                </span>
                                <Lock className="w-3 h-3 text-gray-400 flex-shrink-0" />
                              </div>
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                To: {draft.to || draft.recipient || '(No recipient)'}
                              </p>
                              <div className="flex items-center space-x-2 mt-2 text-xs text-gray-400 dark:text-gray-500">
                                <Clock className="w-3 h-3" />
                                <span>
                                  {new Date(draft.updated_at).toLocaleDateString()} {new Date(draft.updated_at).toLocaleTimeString()}
                                </span>
                              </div>
                            </button>
                            <button
                              onClick={() => deleteDraft(draft.id)}
                              className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                              title="Delete draft"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ============================================ */}
          {/* LINK DIALOG */}
          {/* ============================================ */}
          
          <AnimatePresence>
            {showLinkDialog && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/30"
                onClick={() => setShowLinkDialog(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  onClick={(e) => e.stopPropagation()}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-md"
                >
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Insert Link
                  </h3>
                  <input
                    type="url"
                    value={linkUrl}
                    onChange={(e) => setLinkUrl(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        setLink()
                      }
                    }}
                    placeholder="https://example.com"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
                    autoFocus
                  />
                  <div className="flex items-center justify-end space-x-3">
                    <button
                      onClick={() => {
                        setShowLinkDialog(false)
                        setLinkUrl('')
                      }}
                      className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={setLink}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                    >
                      Insert Link
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </AnimatePresence>
  )
}
