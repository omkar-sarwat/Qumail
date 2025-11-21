import React, { useState, useEffect, useRef, useCallback } from 'react'
import QuantumEmailViewer from '../email/QuantumEmailViewer'
import { 
  Shield, 
  ShieldCheck, 
  Lock, 
  Key,
  Download,
  Eye,
  EyeOff,
  Paperclip,
  Image as ImageIcon,
  File,
  X,
  ChevronUp,
  Star,
  Reply,
  ReplyAll,
  Forward,
  Trash2,
  MoreHorizontal,
  Check
} from 'lucide-react'

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
  body_encrypted?: string
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
  flowId?: string
  flow_id?: string
  gmailMessageId?: string
  gmail_message_id?: string
  gmailThreadId?: string
  gmail_thread_id?: string
  encryption_metadata?: any
  sent_via_gmail?: boolean
  encryptionMethod?: string
  encryption_method?: string
  requires_decryption?: boolean
  decrypt_endpoint?: string
  security_info?: {
    level?: number
    algorithm?: string
    quantum_enhanced?: boolean
    encrypted?: boolean
    flow_id?: string
    flowId?: string
    verification_status?: string
    signature_verified?: boolean
    key_validation?: string
    key_validated?: boolean
    encrypted_size?: number
    encryptedSize?: number
  }
}

interface SecurityBadgeInfo {
  level: number
  algorithm: string
  quantum_enhanced: boolean
  color: string
  icon: React.ReactNode
  description: string
}

interface AttachmentPreview {
  id: string
  name: string
  type: string
  size: number
  url?: string
  thumbnail?: string
  previewUrl?: string
  isImage: boolean
  isVideo: boolean
  isAudio: boolean
  isDocument: boolean
  isArchive: boolean
}

interface ImageModalState {
  isOpen: boolean
  imageUrl: string
  imageName: string
  imageIndex: number
  totalImages: number
}

interface EmailViewerState {
  isSecurityPanelOpen: boolean
  isAttachmentsPanelOpen: boolean
  selectedAttachment: AttachmentPreview | null
  imageModal: ImageModalState
  isStarred: boolean
  isProcessingContent: boolean
  contentHeight: number
  showRawHtml: boolean
  copiedText: string | null
  expandedSections: Set<string>
  attachmentPreviews: AttachmentPreview[]
  inlineImages: string[]
  processedContent: string
  securityInfo: SecurityBadgeInfo | null
}

interface EmailViewerProps {
  email: Email | null
  onReply: () => void
  onReplyAll: () => void
  onForward: () => void
  onDelete: () => void
  onStar?: (starred: boolean) => void
}

export const EmailViewer: React.FC<EmailViewerProps> = ({
  email,
  onReply,
  onReplyAll,
  onForward,
  onDelete,
  onStar
}) => {
  // Complex State Management
  const [state, setState] = useState<EmailViewerState>({
    isSecurityPanelOpen: false,
    isAttachmentsPanelOpen: false,
    selectedAttachment: null,
    imageModal: {
      isOpen: false,
      imageUrl: '',
      imageName: '',
      imageIndex: 0,
      totalImages: 0
    },
    isStarred: false,
    isProcessingContent: true,
    contentHeight: 0,
    showRawHtml: false,
    copiedText: null,
    expandedSections: new Set<string>(),
    attachmentPreviews: [],
    inlineImages: [],
    processedContent: '',
    securityInfo: null
  })

  const contentRef = useRef<HTMLDivElement>(null)
  const processingTimeoutRef = useRef<NodeJS.Timeout>()

  // Security Badge Processing
  const getSecurityBadgeInfo = useCallback((email: Email): SecurityBadgeInfo | null => {
    if (!email.encrypted && !email.securityLevel) return null

    const level = email.securityLevel || email.security_info?.level || 1
    const algorithm = email.encryptionMethod || email.encryption_method || email.security_info?.algorithm || 'Unknown'
    const quantum_enhanced = email.security_info?.quantum_enhanced || false

    const securityConfigs = {
      1: {
        color: 'bg-blue-100 text-blue-800 border-blue-200',
        icon: <Key className="w-4 h-4" />,
        description: 'Quantum OTP Encryption'
      },
      2: {
        color: 'bg-green-100 text-green-800 border-green-200',
        icon: <ShieldCheck className="w-4 h-4" />,
        description: 'AES-256-GCM Quantum Enhanced'
      },
      3: {
        color: 'bg-purple-100 text-purple-800 border-purple-200',
        icon: <Shield className="w-4 h-4" />,
        description: 'Post-Quantum Cryptography'
      },
      4: {
        color: 'bg-red-100 text-red-800 border-red-200',
        icon: <Lock className="w-4 h-4" />,
        description: 'RSA-4096 Hybrid Encryption'
      }
    }

    const config = securityConfigs[level as keyof typeof securityConfigs] || securityConfigs[1]

    return {
      level,
      algorithm,
      quantum_enhanced,
      color: config.color,
      icon: config.icon,
      description: config.description
    }
  }, [])

  // Advanced Attachment Processing
  const processAttachments = useCallback((email: Email): AttachmentPreview[] => {
    if (!email.attachments || email.attachments.length === 0) return []

    return email.attachments.map((attachment, index) => {
      const mimeType = attachment.mimeType || attachment.type || ''
      const name = attachment.filename || attachment.name || `attachment_${index + 1}`
      
      const isImage = mimeType.startsWith('image/')
      const isVideo = mimeType.startsWith('video/')
      const isAudio = mimeType.startsWith('audio/')
      const isDocument = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument'].some(type => mimeType.includes(type))
      const isArchive = ['application/zip', 'application/x-rar', 'application/x-7z'].some(type => mimeType.includes(type))

      return {
        id: attachment.id || `att_${index}`,
        name,
        type: mimeType,
        size: attachment.size || 0,
        url: attachment.url,
        thumbnail: isImage ? attachment.url : undefined,
        previewUrl: attachment.url,
        isImage,
        isVideo,
        isAudio,
        isDocument,
        isArchive
      }
    })
  }, [])

  // Advanced HTML Content Processing
  const processEmailContent = useCallback((email: Email): string => {
    let content = email.bodyHtml || email.html_body || email.bodyText || email.body || email.plain_body || email.snippet || ''
    
    if (!content) return 'No content available'

    // Process inline images
    const imageRegex = /<img[^>]+src="([^"]+)"[^>]*>/gi
    const images: string[] = []
    let match

    while ((match = imageRegex.exec(content)) !== null) {
      images.push(match[1])
    }

    // Add click handlers to images for modal preview
    content = content.replace(imageRegex, (imgTag, src) => {
      const imageIndex = images.indexOf(src)
      return imgTag.replace('<img', `<img data-image-index="${imageIndex}" style="cursor: pointer; max-width: 100%; height: auto;"`)
    })

    // Process links
    content = content.replace(/<a([^>]+)>/gi, '<a$1 target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">')

    // Sanitize and enhance content
    content = content.replace(/<script[^>]*>.*?<\/script>/gi, '')
    content = content.replace(/javascript:/gi, '')
    
    // Remove potentially problematic inline styles that could break layout
    content = content.replace(/position:\s*fixed/gi, 'position: relative')
    content = content.replace(/position:\s*absolute/gi, 'position: relative')
    content = content.replace(/width:\s*100vw/gi, 'width: 100%')
    content = content.replace(/height:\s*100vh/gi, 'height: auto')
    content = content.replace(/min-width:\s*\d+px/gi, 'min-width: auto')
    
    // Wrap content in a constrained container
    content = `<div style="max-width: 100%; overflow: hidden; word-wrap: break-word;">${content}</div>`

    return content
  }, [])

  // Formatted file size display
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }, [])

  // Effects for processing email content and attachments
  useEffect(() => {
    if (!email) return

    setState(prev => ({ ...prev, isProcessingContent: true }))

    // Simulate processing delay for complex content
    processingTimeoutRef.current = setTimeout(() => {
      const securityInfo = getSecurityBadgeInfo(email)
      const attachmentPreviews = processAttachments(email)
      const processedContent = processEmailContent(email)
      const images = processEmailContent(email).match(/<img[^>]+src="([^"]+)"/gi) || []
      const inlineImages = images.map(img => img.match(/src="([^"]+)"/)?.[1] || '').filter(Boolean)

      setState(prev => ({
        ...prev,
        securityInfo,
        attachmentPreviews,
        processedContent,
        inlineImages,
        isProcessingContent: false,
        isStarred: email.isStarred || false,
        isAttachmentsPanelOpen: attachmentPreviews.length > 0
      }))
    }, 300)

    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current)
      }
    }
  }, [email, getSecurityBadgeInfo, processAttachments, processEmailContent])

  // Handle content height calculation
  useEffect(() => {
    if (contentRef.current) {
      const height = contentRef.current.scrollHeight
      setState(prev => ({ ...prev, contentHeight: height }))
    }
  }, [state.processedContent])

  // Action handlers
  const handleStarToggle = useCallback(() => {
    const newStarred = !state.isStarred
    setState(prev => ({ ...prev, isStarred: newStarred }))
    onStar?.(newStarred)
  }, [state.isStarred, onStar])

  const handleImageClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement
    if (target.tagName === 'IMG') {
      const imageIndex = parseInt(target.getAttribute('data-image-index') || '0')
      const imageSrc = target.getAttribute('src') || ''
      const imageName = target.getAttribute('alt') || `Image ${imageIndex + 1}`
      
      setState(prev => ({
        ...prev,
        imageModal: {
          isOpen: true,
          imageUrl: imageSrc,
          imageName,
          imageIndex,
          totalImages: prev.inlineImages.length
        }
      }))
    }
  }, [])

  const handleAttachmentDownload = useCallback(async (attachment: AttachmentPreview) => {
    if (!attachment.url) return
    
    try {
      const link = document.createElement('a')
      link.href = attachment.url
      link.download = attachment.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('Failed to download attachment:', error)
    }
  }, [])

  const closeImageModal = useCallback(() => {
    setState(prev => ({
      ...prev,
      imageModal: { ...prev.imageModal, isOpen: false }
    }))
  }, [])

  const navigateImage = useCallback((direction: 'prev' | 'next') => {
    setState(prev => {
      const currentIndex = prev.imageModal.imageIndex
      const totalImages = prev.imageModal.totalImages
      let newIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1
      
      if (newIndex >= totalImages) newIndex = 0
      if (newIndex < 0) newIndex = totalImages - 1
      
      const newImageUrl = prev.inlineImages[newIndex] || ''
      
      return {
        ...prev,
        imageModal: {
          ...prev.imageModal,
          imageIndex: newIndex,
          imageUrl: newImageUrl,
          imageName: `Image ${newIndex + 1}`
        }
      }
    })
  }, [])
  
  // Only log when we detect potential quantum email for debugging
  const debugLogEmail = (email as any)?.security_level > 0 || (email as any)?.body_encrypted
  if (debugLogEmail) {
    console.log('🔍 EmailViewer received email:', {
      id: email?.id,
      subject: email?.subject,
      body_encrypted: (email as any)?.body_encrypted ? `${(email as any).body_encrypted.substring(0, 50)}...` : null,
      security_level: (email as any)?.security_level,
      security_info: (email as any)?.security_info,
      requires_decryption: email?.requires_decryption,
      flow_id: (email as any)?.flow_id
    })
  }
  
  // Handle encrypted emails with QuantumEmailViewer
  // ONLY show QuantumEmailViewer for emails that were actually quantum-encrypted
  const hasEncryptedPayload = Boolean(
    email &&
      typeof (email as any).body_encrypted === 'string' &&
      (email as any).body_encrypted.trim().length > 0
  )
  const encryptionMetadata = (email as any)?.encryption_metadata
  const hasEncryptionMetadata = Boolean(encryptionMetadata)
  const explicitQuantumFlag = Boolean(email?.requires_decryption)
  const normalizedSecurityLevel = Number(
    (email as any)?.security_level ??
    (email as any)?.securityLevel ??
    (email as any)?.security_info?.level ??
    0
  )
  const hasSecurityLevel = normalizedSecurityLevel > 0
  const hasQuantumMetadata = Boolean(
    hasEncryptionMetadata && (
      encryptionMetadata?.flow_id ||
      encryptionMetadata?.flowId ||
      encryptionMetadata?.algorithm ||
      encryptionMetadata?.encrypted_size ||
      encryptionMetadata?.encryptedSize
    )
  )
  const isQuantumType = (email as any)?.type === 'quantum'

  if (debugLogEmail) {
    console.log('🔍 Quantum detection flags:', {
      hasEncryptedPayload,
      hasQuantumMetadata,
      explicitQuantumFlag,
      hasSecurityLevel,
      isQuantumType
    })
  }
  
  // Route to QuantumEmailViewer whenever the backend marks the email as encrypted
  // or we have clear encrypted payload/metadata to avoid hiding the decrypt button
  const isActuallyQuantumEmail = Boolean(
    hasEncryptedPayload ||
    explicitQuantumFlag ||
    hasQuantumMetadata ||
    hasSecurityLevel ||
    isQuantumType
  )
  
  if (email && isActuallyQuantumEmail) {
    console.log('🔐 Routing to QuantumEmailViewer with email data:', {
      email_id: (email as any).email_id ?? email.id,
      flow_id: (email as any).flow_id,
      security_level: (email as any).security_level,
      encrypted_size: (email as any).encrypted_size,
      security_info: (email as any).security_info,
      encryption_metadata: (email as any).encryption_metadata,
      hasEncryptedPayload,
      hasSecurityLevel,
      explicitQuantumFlag
    })
    
    const quantumEmail = {
      email_id: String((email as any).email_id ?? email.id ?? ''),
      flow_id: (email as any).flow_id ?? (email as any).flowId ?? '',
      sender_email:
        (email as any).sender_email ??
        (email as any).senderEmail ??
        (email as any).from_email ??
        (email as any).sender ??
        '',
      receiver_email:
        (email as any).receiver_email ??
        (email as any).receiverEmail ??
        (email as any).to ??
        (email as any).recipient ??
        '',
      subject: email.subject || '(No Subject)',
      body_encrypted: (email as any).body_encrypted ?? '',
      security_level:
        (email as any).security_level ??
        (email as any).securityLevel ??
        (email as any).security_info?.level ??
        0,
      timestamp: email.timestamp || new Date().toISOString(),
      is_read: (email as any).is_read ?? (email as any).isRead ?? false,
      is_starred: (email as any).is_starred ?? (email as any).isStarred ?? false,
      requires_decryption: true,
      decrypt_endpoint:
        (email as any).decrypt_endpoint ??
        `/api/v1/emails/email/${String((email as any).email_id ?? email.id ?? '')}/decrypt`,
      security_info:
        (email as any).security_info ?? {
          level:
            (email as any).security_level ??
            (email as any).securityLevel ??
            0,
          algorithm:
            (email as any).encryptionMethod ??
            (email as any).encryption_method ??
            (email as any).encryption_metadata?.algorithm ??
            'Unknown',
          quantum_enhanced:
            (email as any).security_info?.quantum_enhanced ?? 
            (email as any).encryption_metadata?.quantum_enhanced ??
            true,
          encrypted_size:
            (email as any).encrypted_size ??
            (email as any).encryptedSize ??
            (email as any).security_info?.encrypted_size ??
            (email as any).encryption_metadata?.encrypted_size ??
            ((email as any).body_encrypted ? (email as any).body_encrypted.length : 0)
        },
      encryption_metadata: (email as any).encryption_metadata
    }

    return <QuantumEmailViewer email={quantumEmail} />
  }

  // Helper functions for email processing
  const getSenderInfo = (email: Email) => {
    const senderName = email.sender_name || email.from_name || 
      (email.sender && email.sender.includes('<') ? 
        email.sender.split('<')[0].trim().replace(/"/g, '') : 
        email.sender?.split('@')[0]) ||
      (email.from && email.from.includes('<') ? 
        email.from.split('<')[0].trim().replace(/"/g, '') : 
        email.from?.split('@')[0]) || 'Unknown Sender'
    
    const senderEmail = email.sender_email || email.from_email || 
      (email.sender && email.sender.includes('<') ? 
        email.sender.split('<')[1]?.replace('>', '').trim() : 
        email.sender) ||
      (email.from && email.from.includes('<') ? 
        email.from.split('<')[1]?.replace('>', '').trim() : 
        email.from) || ''
    
    return { senderName, senderEmail }
  }

  // Show empty state if no email selected
  if (!email) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-[#0d1117]">
        <div className="text-center p-8">
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <ImageIcon className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-1">No Email Selected</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">Select an email from the list to view its contents</p>
        </div>
      </div>
    )
  }

  const { senderName, senderEmail } = getSenderInfo(email)

  return (
    <div className="h-full flex bg-white dark:bg-[#0d1117] overflow-hidden">
      {/* Main Email Content Section */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Professional Action Bar - Outlook Style */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-[#0d1117]">
          <div className="flex items-center gap-3">
            {/* Primary Actions - Professional Style */}
            <div className="flex items-center gap-1">
              <button
                onClick={onReply}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-normal text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title="Reply"
              >
                <Reply className="w-4 h-4" />
                <span>Reply</span>
              </button>
              <button
                onClick={onReplyAll}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-normal text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title="Reply All"
              >
                <ReplyAll className="w-4 h-4" />
                <span>Reply All</span>
              </button>
              <button
                onClick={onForward}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-normal text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title="Forward"
              >
                <Forward className="w-4 h-4" />
                <span>Forward</span>
              </button>
            </div>

            {/* Divider */}
            <div className="h-6 w-px bg-gray-200 dark:bg-gray-700 mx-2"></div>

            {/* Secondary Actions */}
            <div className="flex items-center gap-1">
              <button
                onClick={onDelete}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              
              <button
                onClick={handleStarToggle}
                className={`p-2 rounded transition-colors ${
                  state.isStarred
                    ? 'text-yellow-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                    : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
                title={state.isStarred ? 'Unstar' : 'Star'}
              >
                {state.isStarred ? <Star className="w-4 h-4 fill-current" /> : <Star className="w-4 h-4" />}
              </button>

              <button
                onClick={() => setState(prev => ({ ...prev, showRawHtml: !prev.showRawHtml }))}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title={state.showRawHtml ? 'Show formatted' : 'Show source'}
              >
                {state.showRawHtml ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>

              <button
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title="More options"
              >
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Professional Email Header */}
        <div className="px-8 py-6 border-b border-gray-200 dark:border-gray-700">
          {/* Subject Line */}
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-5 leading-tight">
            {email.subject || "(No Subject)"}
          </h1>

          {/* Sender Information */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              {/* Avatar */}
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-medium text-base flex-shrink-0 shadow-sm">
                {senderName.charAt(0).toUpperCase()}
              </div>
              
              {/* Sender Details */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-semibold text-base text-gray-900 dark:text-white">{senderName}</p>
                  {email.encrypted && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                      <Lock className="w-3 h-3 mr-1" />
                      Encrypted
                    </span>
                  )}
                </div>
                {senderEmail && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">&lt;{senderEmail}&gt;</p>
                )}
                <p className="text-sm text-gray-500 dark:text-gray-500">
                  To: <span className="text-gray-700 dark:text-gray-300">{email.to || email.recipient || 'me'}</span>
                </p>
              </div>
            </div>
            
            {/* Timestamp */}
            <div className="text-sm text-gray-500 dark:text-gray-400 text-right">
              <p className="font-normal">
                {new Date(email.timestamp).toLocaleDateString('en-US', { 
                  weekday: 'short',
                  month: 'short', 
                  day: 'numeric',
                  year: 'numeric'
                })}
              </p>
              <p className="text-gray-400 dark:text-gray-500 mt-0.5">
                {new Date(email.timestamp).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Attachments Section */}
        {state.attachmentPreviews.length > 0 && (
        <div className="px-8 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-[#0d1117]">
          <div className="flex items-center gap-2 mb-3">
            <Paperclip className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {state.attachmentPreviews.length} {state.attachmentPreviews.length === 1 ? 'Attachment' : 'Attachments'}
            </h3>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {state.attachmentPreviews.map((attachment) => (
              <div
                key={attachment.id}
                className="inline-flex items-center gap-2 pl-3 pr-2 py-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm transition-all group"
              >
                <File className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                <div className="flex flex-col min-w-0">
                  <p className="text-sm text-gray-900 dark:text-white truncate max-w-xs">
                    {attachment.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(attachment.size)}
                  </p>
                </div>
                <button
                  onClick={() => handleAttachmentDownload(attachment)}
                  className="flex-shrink-0 p-1.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                  title="Download"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

        {/* Email Content Area */}
        <div className="flex-1 overflow-hidden bg-white dark:bg-[#0d1117]">
        {state.isProcessingContent ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-10 h-10 border-2 border-gray-200 dark:border-gray-700 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Loading message...</p>
            </div>
          </div>
        ) : (
          <div className="h-full overflow-y-auto">
            <div className="max-w-5xl mx-auto px-8 py-8">
              {state.showRawHtml ? (
                <div className="bg-gray-900 dark:bg-black text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-xs">
                  <pre className="whitespace-pre-wrap break-words">
                    {state.processedContent}
                  </pre>
                </div>
              ) : (
                <div 
                  ref={contentRef}
                  className="prose prose-base dark:prose-invert max-w-none 
                    prose-headings:text-gray-900 dark:prose-headings:text-white prose-headings:font-semibold
                    prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:leading-relaxed prose-p:text-[15px]
                    prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline prose-a:font-normal
                    prose-strong:text-gray-900 dark:prose-strong:text-white prose-strong:font-semibold
                    prose-code:text-gray-800 dark:prose-code:text-gray-200 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                    prose-pre:bg-gray-50 dark:prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-gray-800
                    prose-img:rounded-lg prose-img:shadow-sm prose-img:border prose-img:border-gray-200 dark:prose-img:border-gray-700
                    prose-ul:text-gray-700 dark:prose-ul:text-gray-300 prose-ul:leading-relaxed
                    prose-ol:text-gray-700 dark:prose-ol:text-gray-300 prose-ol:leading-relaxed
                    prose-li:text-gray-700 dark:prose-li:text-gray-300 prose-li:text-[15px]
                    prose-blockquote:border-l-4 prose-blockquote:border-l-gray-300 dark:prose-blockquote:border-l-gray-700 prose-blockquote:text-gray-600 dark:prose-blockquote:text-gray-400 prose-blockquote:italic
                    prose-hr:border-gray-200 dark:prose-hr:border-gray-700
                    [&>*]:max-w-full [&_img]:max-w-full [&_img]:h-auto [&_table]:max-w-full [&_table]:overflow-x-auto"
                  style={{ 
                    maxWidth: '100%', 
                    overflow: 'hidden',
                    wordWrap: 'break-word',
                    overflowWrap: 'break-word',
                    lineHeight: '1.7'
                  }}
                  onClick={handleImageClick}
                  dangerouslySetInnerHTML={{ __html: state.processedContent }}
                />
              )}
            </div>
          </div>
        )}
        </div>

        {/* Image Preview Modal */}
        {state.imageModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90 transition-opacity duration-300">
          <div className="relative max-w-4xl max-h-screen p-4">
            {/* Close Button */}
            <button
              onClick={closeImageModal}
              className="absolute top-6 right-6 z-10 p-2 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-70 transition-all duration-200"
            >
              <X className="w-6 h-6" />
            </button>

            {/* Navigation Buttons */}
            {state.imageModal.totalImages > 1 && (
              <>
                <button
                  onClick={() => navigateImage('prev')}
                  className="absolute left-6 top-1/2 transform -translate-y-1/2 z-10 p-3 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-70 transition-all duration-200"
                >
                  <ChevronUp className="w-6 h-6 transform -rotate-90" />
                </button>
                <button
                  onClick={() => navigateImage('next')}
                  className="absolute right-6 top-1/2 transform -translate-y-1/2 z-10 p-3 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-70 transition-all duration-200"
                >
                  <ChevronUp className="w-6 h-6 transform rotate-90" />
                </button>
              </>
            )}

            {/* Image */}
            <img
              src={state.imageModal.imageUrl}
              alt={state.imageModal.imageName}
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            />

            {/* Image Info */}
            <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 text-center text-white">
              <p className="text-lg font-medium mb-1">{state.imageModal.imageName}</p>
              {state.imageModal.totalImages > 1 && (
                <p className="text-sm opacity-75">
                  {state.imageModal.imageIndex + 1} of {state.imageModal.totalImages}
                </p>
              )}
            </div>
          </div>
        </div>
        )}
      </div>

      {/* Right Sidebar - Security Details Panel (Only for Quantum Encrypted Emails - Levels 1, 2, 3) */}
      {(() => {
        // Determine the declared security level and normalize it for comparisons
        const resolveLevel = (value: unknown): number => {
          if (typeof value === 'number') return value
          if (typeof value === 'string') {
            const numeric = value.match(/\d+/)
            if (numeric) {
              return parseInt(numeric[0], 10)
            }

            switch (value.toLowerCase().trim()) {
              case 'rsa':
              case 'rsa-4096':
              case 'standard':
                return 4
              case 'qkd':
              case 'quantum-otp':
              case 'otp':
                return 1
              case 'pqc':
              case 'post-quantum':
              case 'kyber':
                return 3
              case 'aes':
              case 'quantum-aes':
              case 'q-aes':
                return 2
              default:
                return 0
            }
          }
          return 0
        }

        const rawLevelSource = email.securityLevel ?? 
                               (email as any).security_level ?? 
                               email.security_info?.level ??
                               (email as any).securitylevel ??
                               (email as any).level

        let levelNum = resolveLevel(rawLevelSource)
        
        // Level 4 is standard RSA encryption (NOT quantum) - don't show panel
        if (levelNum === 4) {
          console.log('🔐 Security Panel: Hidden (Level 4 - Standard RSA)')
          return null
        }
        
        // Only show panel for explicitly encrypted emails with quantum features (levels 1-3)
        const isExplicitlyEncrypted = email.encrypted === true || 
                                     (email as any).isEncrypted === true ||
                                     email.security_info?.encrypted === true
        
        const hasQuantumEnhancement = email.security_info?.quantum_enhanced === true
        
        const hasEncryptionMetadata = email.security_info?.algorithm || 
                                     (email as any).encryption_method ||
                                     email.security_info?.flow_id ||
                                     (email as any).flow_id
        
        // Show panel ONLY if email is quantum encrypted (levels 1-3)
        const shouldShowPanel = (isExplicitlyEncrypted || hasQuantumEnhancement || hasEncryptionMetadata) && levelNum !== 4
        
        console.log('🔐 Security Panel Check:', {
          emailId: email.id,
          subject: email.subject?.substring(0, 30),
          securityLevel: levelNum,
          encrypted: email.encrypted,
          quantum_enhanced: email.security_info?.quantum_enhanced,
          shouldShowPanel
        })
        
        if (!shouldShowPanel) return null
        
        // Helper to get algorithm name from security level
        function getAlgorithmName(level: number | string): string {
          const numLevel = typeof level === 'string' ? parseInt(level) : level
          switch (numLevel) {
            case 1: return 'OTP-QKD'
            case 2: return 'AES-256-GCM'
            case 3: return 'PQC-Kyber1024'
            case 4: return 'RSA-4096'
            default: return 'AES-256-GCM'
          }
        }

        console.log('🔍 Security Level Debug:', {
          emailId: email.id,
          securityLevel: email.securityLevel,
          security_level: (email as any).security_level,
          security_info_level: email.security_info?.level,
          rawLevel: rawLevelSource,
          emailKeys: Object.keys(email)
        })
        
        const securityLevelNum = levelNum || 2
        
        console.log('✅ Resolved Security Level:', securityLevelNum)

        // Get algorithm - check multiple sources
        const rawAlgorithm = (email as any).encryptionMethod || 
                            (email as any).encryption_method || 
                            email.security_info?.algorithm ||
                            (email as any).algorithm
        const algorithm = rawAlgorithm || getAlgorithmName(securityLevelNum)
        
        // Determine if quantum enhanced (levels 1-2 are quantum)
        const quantumEnhanced = email.security_info?.quantum_enhanced ?? (securityLevelNum <= 2)
        
        // For standard emails (non-encrypted), show as verified since they're from trusted sources (Gmail)
        // For encrypted emails, check actual verification status
        const isEncrypted = email.encrypted === true || 
                           email.security_info?.encrypted === true ||
                           (email as any).isEncrypted === true
        
        const isVerified = isEncrypted 
          ? (email.security_info?.verification_status === 'Verified' || 
             email.security_info?.signature_verified === true || 
             email.encrypted === true)
          : true  // Standard emails from Gmail are verified by default
        
        // Key validation - encrypted emails need validation, standard emails are always valid
        const keyValid = isEncrypted
          ? (email.security_info?.key_validation === 'Valid' || 
             email.security_info?.key_validated === true ||
             email.encrypted === true)
          : true  // Standard emails don't need key validation

        // Get encryption type display
        let encryptionType: string
        let algorithmDisplay: string
        
        if (isEncrypted) {
          // For encrypted emails, show quantum-enhanced or standard based on level
          encryptionType = quantumEnhanced ? 'Quantum-Enhanced' : 'Standard Encryption'
          
          // Format algorithm for display
          if (algorithm.includes('AES')) {
            algorithmDisplay = algorithm.includes('256') ? 'AES-256-GCM' : 'AES-256'
          } else if (algorithm.includes('OTP') || algorithm.includes('QKD')) {
            algorithmDisplay = 'OTP-QKD'
          } else if (algorithm.includes('Kyber') || algorithm.includes('PQC')) {
            algorithmDisplay = 'PQC-Kyber1024'
          } else if (algorithm.includes('RSA')) {
            algorithmDisplay = algorithm.includes('4096') ? 'RSA-4096' : 'RSA-4096'
          } else {
            algorithmDisplay = algorithm
          }
        } else {
          // For standard (non-encrypted) emails
          encryptionType = 'Standard Email'
          algorithmDisplay = 'TLS Transport Security'
        }

        return (
          <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-[#0d1117] overflow-y-auto flex-shrink-0">
          <div className="p-6">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-6">Security Details</h2>            {/* Encryption Type Section */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                Encryption Type
              </label>
              <div className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                    <ShieldCheck className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{encryptionType}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{algorithmDisplay}</p>
                  </div>
                </div>
              </div>
            </div>              {/* Security Level */}
              <div className="mb-5">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Security Level
                </label>
                <div className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Level {securityLevelNum}</span>
                  </div>
                </div>
              </div>

              {/* Key Validation Section */}
              <div className="mb-5">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Key Validation
                </label>
                <div className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    {keyValid ? (
                      <div className="w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-green-600 dark:text-green-400" />
                      </div>
                    ) : (
                      <Key className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                    )}
                    <span className={`text-sm ${
                      keyValid 
                        ? 'text-green-600 dark:text-green-400 font-medium'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      {keyValid ? 'Valid Key' : 'Pending Validation'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Signature Verification Section */}
              <div className="mb-5">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Signature Verification
                </label>
                <div className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    {isVerified ? (
                      <div className="w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-green-600 dark:text-green-400" />
                      </div>
                    ) : (
                      <ShieldCheck className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                    )}
                    <span className={`text-sm ${
                      isVerified 
                        ? 'text-green-600 dark:text-green-400 font-medium'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      {isVerified ? 'Verified' : 'Pending'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}

export default EmailViewer