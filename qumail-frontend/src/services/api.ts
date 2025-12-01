import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios'
import { useAuthStore } from '../stores/authStore'
import { offlineService, LocalEmail } from './offlineService'

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Retry configuration
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
}

export interface EmailsResponse {
  emails: Array<{
    id: string
    threadId: string
    subject: string
    fromAddress: string
    toAddress: string
    ccAddress?: string
    bccAddress?: string
    body: string
    bodyHtml?: string
    securityLevel: 1 | 2 | 3 | 4
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
  }>
  nextPageToken?: string
  totalCount: number
}

export interface UserProfile {
  email: string
  name: string
  picture?: string
  isAuthenticated: boolean
  preferences: {
    defaultSecurityLevel: 1 | 2 | 3 | 4
    autoSaveInterval: number
    theme: 'light' | 'dark' | 'system'
    notifications: boolean
  }
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  timestamp: string
  services: {
    database: 'up' | 'down'
    gmail_api: 'up' | 'down'
    encryption: 'up' | 'down'
    kme_servers: Array<{
      id: string
      status: 'connected' | 'disconnected'
      latency?: number
    }>
  }
  metrics: {
    totalEmails: number
    encryptedEmails: number
    activeUsers: number
    uptime: number
  }
}

class ApiService {
  private api: AxiosInstance
  private baseURL: string
  private token: string | null = null

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    
    if (import.meta.env.DEV) {
      console.log('API Service initialized with baseURL:', this.baseURL)
    }
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token =
          this.token ||
          useAuthStore.getState().sessionToken ||
          localStorage.getItem('authToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        console.error('Request interceptor error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor with retry logic and better error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retryCount?: number }
        
        // Don't retry or redirect if offline
        if (!navigator.onLine || error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
          if (import.meta.env.DEV) {
            console.log('[API] Network error while offline - not retrying')
          }
          return Promise.reject(error)
        }
        
        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          if (navigator.onLine) {
            console.log('[API] Got 401 while online - logging out')
            useAuthStore.getState().logout()
            window.location.href = '/'
          }
          return Promise.reject(error)
        }
        
        // Retry logic for retryable errors
        if (originalRequest && RETRY_CONFIG.retryableStatuses.includes(error.response?.status || 0)) {
          const retryCount = originalRequest._retryCount || 0
          
          if (retryCount < RETRY_CONFIG.maxRetries) {
            originalRequest._retryCount = retryCount + 1
            
            // Exponential backoff
            const delay = RETRY_CONFIG.retryDelay * Math.pow(2, retryCount)
            await new Promise(resolve => setTimeout(resolve, delay))
            
            if (import.meta.env.DEV) {
              console.log(`[API] Retrying request (${retryCount + 1}/${RETRY_CONFIG.maxRetries})`)
            }
            
            return this.api(originalRequest)
          }
        }
        
        return Promise.reject(error)
      }
    )
  }

  // Helper to ensure consistent API version prefix
  private withPrefix(path: string): string {
    if (path.startsWith('/api/')) return path // already fully qualified
    return `/api/v1${path}`
  }

  // Health and Status
  async getHealth(): Promise<HealthStatus> {
    const response = await this.api.get<HealthStatus>(this.withPrefix('/health'))
    return response.data
  }

  async getDetailedHealth(): Promise<HealthStatus> {
    const response = await this.api.get<HealthStatus>(this.withPrefix('/health/detailed'))
    return response.data
  }

  // Authentication
  async getAuthUrl(): Promise<{ auth_url: string }> {
    const response = await this.api.get<{ auth_url: string }>(this.withPrefix('/auth/url'))
    return response.data
  }

  async exchangeCode(code: string): Promise<{ access_token: string; user: UserProfile }> {
    const response = await this.api.post<{ access_token: string; user: UserProfile }>(this.withPrefix('/auth/callback'), {
      code,
    })
    return response.data
  }

  async getUserProfile(): Promise<UserProfile> {
    const response = await this.api.get<UserProfile>(this.withPrefix('/auth/profile'))
    return response.data
  }

  async refreshToken(): Promise<{ access_token: string }> {
    const response = await this.api.post<{ access_token: string }>(this.withPrefix('/auth/refresh'))
    return response.data
  }

  async logout(): Promise<void> {
    await this.api.post(this.withPrefix('/auth/logout'))
  }

  // ==================== OFFLINE-FIRST EMAIL OPERATIONS ====================

  /**
   * Get emails with offline-first approach:
   * 1. First, get emails from local SQLite database (instant)
   * 2. If online, fetch from server in background and update local DB
   * 3. Return merged results
   */
  async getEmails(params: {
    folder?: string
    securityLevel?: 1 | 2 | 3 | 4
    searchQuery?: string
    isRead?: boolean
    hasAttachments?: boolean
    pageToken?: string
    maxResults?: number
  } = {}): Promise<EmailsResponse> {
    const {
      folder = 'inbox',
      pageToken,
      maxResults = 50,
      ...rest
    } = params

    // Step 1: Try to get from local database first (if in Electron)
    let localEmails: any[] = []
    if (offlineService.isElectronApp) {
      try {
        const localData = await offlineService.getLocalEmails(folder, maxResults, 0)
        localEmails = localData.map(this.convertLocalEmailToResponse)
        console.log(`📦 Loaded ${localEmails.length} emails from local database`)
      } catch (error) {
        console.warn('Failed to get local emails:', error)
      }
    }

    // Step 2: If online, fetch from server
    if (offlineService.isOnline) {
      try {
        const query: Record<string, any> = { ...rest }
        if (pageToken) query.page_token = pageToken
        if (typeof maxResults !== 'undefined') query.max_results = maxResults

        const response = await this.api.get<any>(
          this.withPrefix(`/emails/${folder}`),
          { params: query }
        )

        const data = response.data ?? {}
        const serverEmails = data.emails ?? []

        // Step 3: Save server emails to local database
        if (offlineService.isElectronApp && serverEmails.length > 0) {
          const localFormat = serverEmails.map((email: any) => 
            offlineService.convertServerEmailToLocal({ ...email, folder })
          )
          await offlineService.saveEmailsLocally(localFormat)
          console.log(`💾 Saved ${serverEmails.length} emails to local database`)
        }

        return {
          emails: serverEmails,
          nextPageToken: data.next_page_token ?? data.nextPageToken,
          totalCount: data.total_count ?? data.totalCount ?? serverEmails.length,
        }
      } catch (error) {
        console.warn('Failed to fetch from server, using local data:', error)
        // Fall back to local data if server fails
        if (localEmails.length > 0) {
          return {
            emails: localEmails,
            nextPageToken: undefined,
            totalCount: localEmails.length
          }
        }
        throw error
      }
    }

    // Offline mode - return local data only
    console.log('📴 Offline mode - using local database only')
    return {
      emails: localEmails,
      nextPageToken: undefined,
      totalCount: localEmails.length
    }
  }

  /**
   * Convert local email format to API response format
   */
  private convertLocalEmailToResponse(email: LocalEmail): any {
    return {
      id: email.id,
      threadId: email.thread_id,
      subject: email.subject,
      fromAddress: email.sender_email,
      from_name: email.sender_name,
      toAddress: email.recipient_email,
      body: email.is_decrypted ? email.decrypted_content : email.body,
      bodyHtml: email.is_decrypted ? email.decrypted_html : email.body_html,
      bodyEncrypted: email.body_encrypted,
      snippet: email.snippet,
      securityLevel: email.security_level,
      timestamp: email.timestamp,
      isRead: email.is_read,
      isStarred: email.is_starred,
      isEncrypted: email.is_encrypted,
      isDecrypted: email.is_decrypted,
      globallyDecrypted: email.globally_decrypted,
      flowId: email.flow_id,
      security_info: email.security_info ? JSON.parse(email.security_info) : undefined,
      requires_decryption: email.is_encrypted && !email.is_decrypted,
      labels: [],
      hasAttachments: !!email.attachments,
      attachments: email.attachments ? JSON.parse(email.attachments) : [],
      // Flag to indicate this came from local cache
      _fromLocalCache: true
    }
  }

  async getEmailDetails(emailId: string): Promise<any> {
    // Try local first
    if (offlineService.isElectronApp) {
      const localEmail = await offlineService.getLocalEmail(emailId)
      if (localEmail) {
        console.log(`📦 Loaded email details from local database: ${emailId}`)
        return this.convertLocalEmailToResponse(localEmail)
      }
    }

    // Fetch from server
    const response = await this.api.get(this.withPrefix(`/emails/email/${emailId}`))
    
    // Save to local database
    if (offlineService.isElectronApp && response.data) {
      await offlineService.saveEmailLocally(
        offlineService.convertServerEmailToLocal(response.data)
      )
    }
    
    return response.data
  }

  async markEmailAsRead(emailId: string, isRead: boolean): Promise<void> {
    // Update local database immediately
    if (offlineService.isElectronApp) {
      await offlineService.markAsReadLocally(emailId, isRead)
    }

    // If online, also update server
    if (offlineService.isOnline) {
      await this.api.post(this.withPrefix(`/emails/${emailId}/read`), { isRead })
    }
    // If offline, the change is queued in the local database sync queue
  }

  async toggleEmailStar(emailId: string, isStarred: boolean): Promise<void> {
    // Update local database immediately
    if (offlineService.isElectronApp) {
      await offlineService.markAsStarredLocally(emailId, isStarred)
    }

    // If online, also update server
    if (offlineService.isOnline) {
      await this.api.patch(this.withPrefix(`/emails/${emailId}/star`), { isStarred })
    }
    // If offline, the change is queued in the local database sync queue
  }

  async deleteEmail(emailId: string): Promise<void> {
    await this.api.delete(this.withPrefix(`/emails/${emailId}`))
  }

  async moveEmailToTrash(emailId: string): Promise<void> {
    await this.api.post(this.withPrefix(`/emails/${emailId}/trash`))
  }

  async archiveEmail(emailId: string): Promise<void> {
    await this.api.post(this.withPrefix(`/emails/${emailId}/archive`))
  }

  // Compose and Send
  async sendEmail(emailData: {
    to: string
    cc?: string
    bcc?: string
    subject: string
    body: string
    isHtml: boolean
    securityLevel: 1 | 2 | 3 | 4
    attachments?: File[]
    isScheduled?: boolean
    scheduledDate?: string
  }): Promise<{ messageId: string }> {
    const formData = new FormData()
    
    // Add text fields
    formData.append('to', emailData.to)
    if (emailData.cc) formData.append('cc', emailData.cc)
    if (emailData.bcc) formData.append('bcc', emailData.bcc)
    formData.append('subject', emailData.subject)
    formData.append('body', emailData.body)
    formData.append('isHtml', emailData.isHtml.toString())
    formData.append('securityLevel', emailData.securityLevel.toString())
    
    // Add attachments
    if (emailData.attachments) {
      emailData.attachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file)
      })
    }

    const response = await this.api.post<{ messageId: string }>(this.withPrefix('/emails/send'), formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async scheduleEmail(emailData: {
    to: string
    cc?: string
    bcc?: string
    subject: string
    body: string
    isHtml: boolean
    securityLevel: 1 | 2 | 3 | 4
    attachments?: File[]
    scheduledDate: string
  }): Promise<{ scheduledId: string }> {
    const formData = new FormData()
    
    // Add all email fields
    formData.append('to', emailData.to)
    if (emailData.cc) formData.append('cc', emailData.cc)
    if (emailData.bcc) formData.append('bcc', emailData.bcc)
    formData.append('subject', emailData.subject)
    formData.append('body', emailData.body)
    formData.append('isHtml', emailData.isHtml.toString())
    formData.append('securityLevel', emailData.securityLevel.toString())
    formData.append('scheduledDate', emailData.scheduledDate)
    
    // Add attachments
    if (emailData.attachments) {
      emailData.attachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file)
      })
    }

    const response = await this.api.post<{ scheduledId: string }>(this.withPrefix('/emails/schedule'), formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // Drafts
  async getDrafts(): Promise<EmailsResponse> {
    const response = await this.api.get<EmailsResponse>(this.withPrefix('/drafts'))
    return response.data
  }

  async getDraft(draftId: string): Promise<any> {
    const response = await this.api.get(this.withPrefix(`/drafts/${draftId}`))
    return response.data
  }

  async saveDraft(draftData: {
    to: string
    cc?: string
    bcc?: string
    subject: string
    body: string
    isHtml: boolean
    securityLevel: 1 | 2 | 3 | 4
    attachments?: File[]
    scheduledDate?: string
  }): Promise<{ id: string }> {
    const formData = new FormData()
    
    // Add text fields
    formData.append('to', draftData.to)
    if (draftData.cc) formData.append('cc', draftData.cc)
    if (draftData.bcc) formData.append('bcc', draftData.bcc)
    formData.append('subject', draftData.subject)
    formData.append('body', draftData.body)
    formData.append('isHtml', draftData.isHtml.toString())
    formData.append('securityLevel', draftData.securityLevel.toString())
    if (draftData.scheduledDate) formData.append('scheduledDate', draftData.scheduledDate)
    
    // Add attachments
    if (draftData.attachments) {
      draftData.attachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file)
      })
    }

    const response = await this.api.post<{ id: string }>(this.withPrefix('/drafts'), formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async updateDraft(draftId: string, draftData: any): Promise<{ id: string }> {
    const formData = new FormData()
    
    // Add all fields
    Object.keys(draftData).forEach(key => {
      if (key === 'attachments' && draftData[key]) {
        draftData[key].forEach((file: File, index: number) => {
          formData.append(`attachment_${index}`, file)
        })
      } else if (draftData[key] !== undefined) {
        formData.append(key, draftData[key].toString())
      }
    })

    const response = await this.api.put<{ id: string }>(this.withPrefix(`/drafts/${draftId}`), formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async deleteDraft(draftId: string): Promise<void> {
    await this.api.delete(this.withPrefix(`/drafts/${draftId}`))
  }

  // Attachments
  async downloadAttachment(emailId: string, attachmentId: string): Promise<Blob> {
    const response = await this.api.get(this.withPrefix(`/emails/${emailId}/attachments/${attachmentId}`), {
      responseType: 'blob',
    })
    return response.data
  }

  // Search
  async searchEmails(query: string, filters?: {
    folder?: string
    securityLevel?: number
    dateRange?: { start: string; end: string }
  }): Promise<EmailsResponse> {
    const response = await this.api.get<EmailsResponse>(this.withPrefix('/emails/search'), {
      params: { q: query, ...filters },
    })
    return response.data
  }

  // Real KM Status from Next Door Key Simulator
  async getKMStatus(): Promise<{
    timestamp: string
    simulator_type: string
    etsi_standard: string
    kme_servers: {
      kme1: {
        url: string
        kme_id: string
        local_sae_id: string
        peer_sae_id: string
        status: 'online' | 'offline'
        available_keys: number
        max_keys_per_request: number
        max_key_size: number
        min_key_size: number
        default_key_size: number
        last_check: string
        error?: string
      }
      kme2: {
        url: string
        kme_id: string
        local_sae_id: string
        peer_sae_id: string
        status: 'online' | 'offline'
        available_keys: number
        max_keys_per_request: number
        max_key_size: number
        min_key_size: number
        default_key_size: number
        last_check: string
        error?: string
      }
    }
    summary: {
      total_available_keys: number
      online_kmes: number
      total_kmes: number
      system_health: 'healthy' | 'degraded' | 'offline'
    }
  }> {
    const response = await this.api.get(this.withPrefix('/km/status'))
    return response.data
  }

  async getAvailableKeys(): Promise<{
    timestamp: string
    kme_keys: {
      kme1: {
        kme_url: string
        local_sae_id: string
        peer_sae_id: string
        available_keys: number
        max_per_request: number
        key_size_bytes: number
        max_key_size: number
        min_key_size: number
        status: 'online' | 'offline'
        error?: string
      }
      kme2: {
        kme_url: string
        local_sae_id: string
        peer_sae_id: string
        available_keys: number
        max_per_request: number
        key_size_bytes: number
        max_key_size: number
        min_key_size: number
        status: 'online' | 'offline'
        error?: string
      }
    }
  }> {
    const response = await this.api.get(this.withPrefix('/km/keys/available'))
    return response.data
  }

  async requestTestKeys(numberOfKeys: number = 1): Promise<{
    timestamp: string
    requested_keys: number
    received_keys: number
    keys_metadata: Array<{
      key_id: string
      key_size_bits: number
      source_kme: string
    }>
  }> {
    const response = await this.api.post(this.withPrefix('/km/keys/request-test'), {
      number_of_keys: numberOfKeys
    })
    return response.data
  }

  async testEncryption(level: 1 | 2 | 3 | 4, message: string): Promise<{
    encrypted: string
    decrypted: string
    timeTaken: number
    keyUsed: string
  }> {
    const response = await this.api.post(this.withPrefix('/encryption/test'), {
      level,
      message,
    })
    return response.data
  }

  // Preferences
  async updatePreferences(preferences: Partial<UserProfile['preferences']>): Promise<UserProfile> {
    const response = await this.api.patch<UserProfile>('/auth/preferences', preferences)
    return response.data
  }

  // Notifications
  async getNotifications(): Promise<Array<{
    id: string
    type: 'info' | 'warning' | 'error' | 'success'
    title: string
    message: string
    timestamp: string
    isRead: boolean
  }>> {
    const response = await this.api.get(this.withPrefix('/notifications'))
    return response.data
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    await this.api.patch(this.withPrefix(`/notifications/${notificationId}/read`))
  }

  // Statistics
  async getEmailStats(period: 'day' | 'week' | 'month' | 'year' = 'week'): Promise<{
    totalEmails: number
    sentEmails: number
    receivedEmails: number
    encryptionBreakdown: {
      quantum_otp: number
      quantum_aes: number
      post_quantum: number
      standard_rsa: number
    }
    securityThreats: number
    avgResponseTime: number
  }> {
    const response = await this.api.get(this.withPrefix('/stats/emails'), {
      params: { period },
    })
    return response.data
  }

  // Authentication Helper Methods
  setAuthToken(token: string): void {
    this.token = token
  }

  clearAuthToken(): void {
    this.token = null
  }

  async validateAuth(): Promise<{ isAuthenticated: boolean; email: string; name?: string }> {
    // Reuse user profile endpoint; treat success as authenticated
    const profile = await this.getUserProfile()
    return { isAuthenticated: true, email: profile.email, name: profile.name }
  }

  async getGoogleAuthUrl(): Promise<{ auth_url: string }> {
    try {
      const response = await this.api.get<{ authorization_url: string }>(this.withPrefix('/auth/google'))
      return { auth_url: response.data.authorization_url }
    } catch (error) {
      console.error('getGoogleAuthUrl error:', error)
      throw error
    }
  }

  async handleOAuthCallback(code: string, state: string): Promise<{ user_email: string; session_token: string; expires_at: string }> {
    const response = await this.api.post<{ user_email: string; session_token: string; expires_at: string }>(this.withPrefix('/auth/callback'), { code, state })
    return response.data
  }

  // Email folders (for sidebar)
  async getEmailFolders(): Promise<Array<{ id: string; name: string; count?: number }>> {
    const response = await this.api.get<Array<{ id: string; name: string; count?: number }>>(this.withPrefix('/emails/folders'))
    return response.data
  }
}

export const apiService = new ApiService()
export default apiService