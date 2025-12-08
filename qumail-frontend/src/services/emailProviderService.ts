/**
 * Email provider service
 * 
 * Routes email operations to the appropriate backend:
 * - Gmail accounts: Use Gmail API (OAuth-based)
 * - Other providers: Use IMAP/POP3/SMTP (multi-provider API)
 */

import { apiService } from './api'
import { useEmailAccountsStore } from '../stores/emailAccountsStore'
import { getPassword } from '../utils/credentialStorage'

export interface EmailMessage {
  id: string
  threadId: string
  subject: string
  fromAddress: string
  fromName: string
  toAddress: string
  toName: string
  ccAddress?: string
  body: string
  bodyHtml?: string
  timestamp: string
  isRead: boolean
  hasAttachments: boolean
  folder: string
  securityLevel?: number
}

export interface SendEmailData {
  to: string
  subject: string
  body: string
  bodyHtml?: string
  cc?: string
  bcc?: string
  securityLevel?: number
}

class EmailProviderService {
  /**
   * Get the active account with credentials
   */
  private getActiveAccountWithCredentials() {
    const store = useEmailAccountsStore.getState()
    const { accounts, activeAccountId } = store
    
    const account = accounts.find((acc) => acc.id === activeAccountId)
    if (!account) return null
    
    const password = getPassword(account.id)
    if (!password) return null
    
    return {
      email: account.email,
      password,
      displayName: account.displayName,
      provider: account.provider,
      settings: {
        smtp_host: account.settings.smtp_host,
        smtp_port: account.settings.smtp_port,
        smtp_security: account.settings.smtp_security,
        imap_host: account.settings.imap_host,
        imap_port: account.settings.imap_port,
        imap_security: account.settings.imap_security,
        protocol: account.settings.protocol,
      },
      foldersToSync: account.foldersToSync,
    }
  }

  /**
   * Check if using Gmail account (uses OAuth API)
   */
  isGmailAccount(): boolean {
    const store = useEmailAccountsStore.getState()
    const { accounts, activeAccountId } = store
    const account = accounts.find((acc) => acc.id === activeAccountId)
    
    if (!account) {
      // No provider account configured, use default Gmail OAuth
      return true
    }
    
    return account.provider === 'Gmail' || account.email.endsWith('@gmail.com')
  }

  /**
   * Fetch emails from the active account
   */
  async fetchEmails(options: {
    folder?: string
    maxResults?: number
    offset?: number
    pageToken?: string
  } = {}): Promise<{
    emails: EmailMessage[]
    nextPageToken?: string
    totalCount: number
  }> {
    const account = this.getActiveAccountWithCredentials()
    
    // If no provider account or Gmail, use default Gmail API
    if (!account || this.isGmailAccount()) {
      const response = await apiService.getEmails({
        folder: options.folder || 'inbox',
        maxResults: options.maxResults || 50,
        pageToken: options.pageToken,
      })
      
      return {
        emails: (response.emails || []).map((e: any) => ({
          id: e.id,
          threadId: e.threadId || e.id,
          subject: e.subject || '(No subject)',
          fromAddress: e.fromAddress || e.sender,
          fromName: e.sender || e.fromAddress?.split('@')[0] || '',
          toAddress: e.toAddress || e.recipient,
          toName: e.recipient || e.toAddress?.split('@')[0] || '',
          ccAddress: e.ccAddress,
          body: e.body || e.bodyText || '',
          bodyHtml: e.bodyHtml,
          timestamp: e.timestamp || new Date().toISOString(),
          isRead: e.isRead ?? true,
          hasAttachments: e.hasAttachments ?? false,
          folder: options.folder || 'inbox',
          securityLevel: e.securityLevel,
        })),
        nextPageToken: response.nextPageToken,
        totalCount: response.totalCount || 0,
      }
    }
    
    // Use multi-provider API
    const response = await apiService.fetchProviderEmails(account, {
      folder: options.folder || 'INBOX',
      maxResults: options.maxResults || 50,
      offset: options.offset || 0,
    })
    
    return {
      emails: response.emails.map((e) => ({
        id: e.id,
        threadId: e.thread_id,
        subject: e.subject,
        fromAddress: e.from_address,
        fromName: e.from_name,
        toAddress: e.to_address,
        toName: e.to_name,
        ccAddress: e.cc_address || undefined,
        body: e.body_text,
        bodyHtml: e.body_html || undefined,
        timestamp: e.timestamp,
        isRead: e.is_read,
        hasAttachments: e.has_attachments,
        folder: e.folder,
      })),
      totalCount: response.total_count,
    }
  }

  /**
   * Send email from the active account
   */
  async sendEmail(emailData: SendEmailData): Promise<{
    success: boolean
    messageId?: string
    message: string
  }> {
    const account = this.getActiveAccountWithCredentials()
    
    // If no provider account or Gmail, use default Gmail API
    if (!account || this.isGmailAccount()) {
      const secLevel = (emailData.securityLevel || 1) as 1 | 2 | 3 | 4
      const response = await apiService.sendEmail({
        to: emailData.to,
        subject: emailData.subject,
        body: emailData.body,
        isHtml: !!emailData.bodyHtml,
        cc: emailData.cc,
        bcc: emailData.bcc,
        securityLevel: secLevel,
      })
      
      return {
        success: true,
        messageId: response.messageId,
        message: 'Email sent via Gmail',
      }
    }
    
    // Use multi-provider API
    const response = await apiService.sendProviderEmail(account, {
      to_address: emailData.to,
      subject: emailData.subject,
      body_text: emailData.body,
      body_html: emailData.bodyHtml,
      cc_address: emailData.cc,
      bcc_address: emailData.bcc,
      security_level: emailData.securityLevel || 0,
    })
    
    return {
      success: response.success,
      messageId: response.message_id || undefined,
      message: response.message,
    }
  }

  /**
   * Mark email as read
   */
  async markAsRead(emailId: string, folder: string = 'INBOX'): Promise<void> {
    const account = this.getActiveAccountWithCredentials()
    
    if (!account || this.isGmailAccount()) {
      // Gmail API handles this differently
      // await apiService.markAsRead(emailId)
      return
    }
    
    await apiService.markProviderEmailRead(account, emailId, folder)
  }

  /**
   * Delete email
   */
  async deleteEmail(emailId: string, folder: string = 'INBOX'): Promise<void> {
    const account = this.getActiveAccountWithCredentials()
    
    if (!account || this.isGmailAccount()) {
      // Gmail API
      await apiService.deleteEmail(emailId)
      return
    }
    
    await apiService.deleteProviderEmail(account, emailId, folder)
  }

  /**
   * List available folders
   */
  async listFolders(): Promise<string[]> {
    const account = this.getActiveAccountWithCredentials()
    
    if (!account || this.isGmailAccount()) {
      // Gmail uses labels
      return ['INBOX', 'Sent', 'Drafts', 'Spam', 'Trash']
    }
    
    const response = await apiService.listProviderFolders(account)
    return response.folders
  }

  /**
   * Get account display info
   */
  getAccountInfo(): {
    email: string
    displayName: string
    provider: string
  } | null {
    const store = useEmailAccountsStore.getState()
    const { accounts, activeAccountId } = store
    const account = accounts.find((acc) => acc.id === activeAccountId)
    
    if (!account) return null
    
    return {
      email: account.email,
      displayName: account.displayName,
      provider: account.provider,
    }
  }
}

export const emailProviderService = new EmailProviderService()
export default emailProviderService
