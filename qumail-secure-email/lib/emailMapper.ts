import { Email, EmailAttachment, SecurityLevel } from '../types'

const SECURITY_LEVEL_LABEL: Record<number, SecurityLevel> = {
  1: SecurityLevel.LEVEL_1,
  2: SecurityLevel.LEVEL_2,
  3: SecurityLevel.LEVEL_3,
  4: SecurityLevel.LEVEL_4,
}

const MONTH_FORMAT: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' }
const TIME_FORMAT: Intl.DateTimeFormatOptions = { hour: 'numeric', minute: '2-digit' }

function ensureDate(value?: string): Date {
  if (!value) return new Date()
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return new Date()
  }
  return parsed
}

function formatTimestamp(value?: string) {
  const date = ensureDate(value)
  return {
    timestamp: new Intl.DateTimeFormat('en-US', TIME_FORMAT).format(date),
    fullDate: new Intl.DateTimeFormat('en-US', MONTH_FORMAT).format(date),
  }
}

function normalizeSecurityLevel(value?: number | string | null): SecurityLevel {
  if (typeof value === 'number' && SECURITY_LEVEL_LABEL[value]) {
    return SECURITY_LEVEL_LABEL[value]
  }

  if (typeof value === 'string') {
    const normalized = value.toLowerCase()
    if (normalized.includes('level 1')) return SecurityLevel.LEVEL_1
    if (normalized.includes('level 2')) return SecurityLevel.LEVEL_2
    if (normalized.includes('level 3')) return SecurityLevel.LEVEL_3
  }

  return SecurityLevel.LEVEL_4
}

function parseAddress(raw?: string) {
  if (!raw) return { name: 'Unknown Sender', email: '' }
  const match = raw.match(/^(.*)<(.+)>$/)
  if (match) {
    return {
      name: match[1].trim().replace(/"/g, '') || match[2].trim(),
      email: match[2].trim(),
    }
  }
  return { name: raw.trim(), email: raw.trim() }
}

function deriveAvatar(name: string, email: string) {
  if (name && name.length <= 4) {
    return name
  }
  if (email) {
    return email[0].toUpperCase()
  }
  return 'Q'
}

function mapAttachments(list?: any[]): EmailAttachment[] | undefined {
  if (!Array.isArray(list) || !list.length) return undefined
  return list.map((item, index) => ({
    id: item.id || item.attachmentId || `att-${index}`,
    filename: item.filename || item.name || `attachment-${index + 1}`,
    mimeType: item.mimeType || item.contentType,
    size: item.size || item.length,
    content: item.content,
  }))
}

function deriveTags(summary: any, isEncrypted: boolean): string[] {
  const tags = new Set<string>()
  if (Array.isArray(summary.labels)) {
    summary.labels.forEach((label: string) => {
      if (label) tags.add(label.toUpperCase())
    })
  }
  if (isEncrypted) {
    tags.add('QUANTUM')
  }
  return Array.from(tags)
}

export function mapSummaryToEmail(summary: any, folder: string): Email {
  const senderValue = summary.sender || summary.from || summary.fromAddress || summary.sender_email
  const { name: senderName, email: senderEmail } = parseAddress(senderValue)
  const times = formatTimestamp(summary.timestamp || summary.date || summary.receivedDate)
  const isEncrypted = Boolean(summary.encrypted ?? summary.requires_decryption ?? (summary.security_level && summary.security_level > 0))
  const securityLevel = normalizeSecurityLevel(summary.security_level ?? summary.securityLevel ?? (isEncrypted ? 2 : 4))
  const unreadFlag =
    summary.isUnread ??
    summary.is_unread ??
    (typeof summary.read === 'boolean' ? summary.read === false : undefined)

  return {
    id: summary.id || summary.flow_id || summary.email_id || summary.gmailMessageId || summary.messageId || crypto.randomUUID(),
    senderName,
    senderEmail,
    senderAvatar: deriveAvatar(senderName, senderEmail),
    subject: summary.subject || '(No subject)',
    snippet: summary.snippet || summary.bodyText || '',
    content: '',
    timestamp: times.timestamp,
    fullDate: times.fullDate,
    tags: deriveTags(summary, isEncrypted),
    isUnread: unreadFlag ?? false,
    isStarred: summary.isStarred ?? summary.is_starred ?? false,
    securityLevel,
    isEncrypted,
    folder: folder as Email['folder'],
    securityDetails: summary.flow_id
      ? {
          flowId: summary.flow_id,
          signatureVerified: true,
        }
      : undefined,
    flowId: summary.flow_id,
    gmailMessageId: summary.gmail_message_id || summary.gmailMessageId,
    requiresDecryption: summary.requires_decryption ?? false,
    decryptEndpoint: summary.decrypt_endpoint,
  }
}

export function mergeDetail(email: Email, detail: any): Email {
  const payload = detail.email_data ? detail.email_data : detail
  const { name: senderName, email: senderEmail } = parseAddress(payload.sender || payload.sender_email || email.senderEmail)
  const times = formatTimestamp(payload.timestamp || detail.timestamp)
  const requiresDecryption = Boolean(detail.requires_decryption ?? email.requiresDecryption)

  return {
    ...email,
    senderName,
    senderEmail,
    senderAvatar: email.senderAvatar || deriveAvatar(senderName, senderEmail),
    content: payload.bodyHtml || payload.body || detail.bodyHtml || detail.body || email.content,
    bodyHtml: payload.bodyHtml || detail.bodyHtml || email.bodyHtml,
    attachments: mapAttachments(detail.attachments || payload.attachments) || email.attachments,
    timestamp: times.timestamp,
    fullDate: times.fullDate,
    flowId: detail.flow_id || payload.flow_id || email.flowId,
    gmailMessageId: payload.gmail_message_id || email.gmailMessageId,
    requiresDecryption,
    decryptEndpoint: detail.decrypt_endpoint || email.decryptEndpoint,
    securityDetails: (detail.flow_id || payload.flow_id)
      ? {
          flowId: detail.flow_id || payload.flow_id,
          signatureVerified: detail.security_info?.verification_status !== 'failed',
        }
      : email.securityDetails,
    isEncrypted: email.isEncrypted,
  }
}

export function applyDecryption(email: Email, result: any): Email {
  const payload = result.email_data || {}
  const times = formatTimestamp(payload.timestamp)

  return {
    ...email,
    content: payload.body || email.content,
    bodyHtml: payload.bodyHtml || email.bodyHtml,
    attachments: mapAttachments(payload.attachments) || email.attachments,
    timestamp: times.timestamp,
    fullDate: times.fullDate,
    flowId: payload.flow_id || email.flowId,
    requiresDecryption: false,
    securityDetails: payload.flow_id
      ? {
          flowId: payload.flow_id,
          signatureVerified: result.security_info?.verification_status !== 'failed',
        }
      : email.securityDetails,
  }
}
