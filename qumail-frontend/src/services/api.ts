import axios, { AxiosInstance } from 'axios'
import { useAuthStore } from '../stores/authStore'

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
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
    
    console.log('API Service initialized with baseURL:', this.baseURL)
    
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
          localStorage.getItem('authToken') ||
          'VALID_ACCESS_TOKEN'  // Test token fallback for development
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

    // Response interceptor to handle auth errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          useAuthStore.getState().logout()
          window.location.href = '/'
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

  // Emails
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
      maxResults,
      ...rest
    } = params

    const query: Record<string, any> = { ...rest }
    if (pageToken) query.page_token = pageToken
    if (typeof maxResults !== 'undefined') query.max_results = maxResults

    const response = await this.api.get<any>(
      this.withPrefix(`/emails/${folder}`),
      { params: query }
    )

    const data = response.data ?? {}

    return {
      emails: data.emails ?? [],
      nextPageToken: data.next_page_token ?? data.nextPageToken,
      totalCount: data.total_count ?? data.totalCount ?? (data.emails ? data.emails.length : 0),
    }
  }

  async getEmailDetails(emailId: string): Promise<any> {
    const response = await this.api.get(this.withPrefix(`/emails/email/${emailId}`))
    return response.data
  }

  async markEmailAsRead(emailId: string, isRead: boolean): Promise<void> {
    await this.api.post(this.withPrefix(`/emails/${emailId}/read`), { isRead })
  }

  async toggleEmailStar(emailId: string, isStarred: boolean): Promise<void> {
    await this.api.patch(this.withPrefix(`/emails/${emailId}/star`), { isStarred })
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