import axios from 'axios';
import { offlineService } from './offlineService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://qumail-backend-gwec.onrender.com';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface SendQuantumEmailRequest {
  to: string | string[];
  subject: string;
  body: string;
  security_level: number;
  cc?: string[];
  bcc?: string[];
  priority?: string;
}

export interface QuantumEmail {
  email_id: number;
  flow_id: string;
  sender_email: string;
  receiver_email: string;
  subject: string;
  body_encrypted: string;
  security_level: number;
  timestamp: string;
  is_read: boolean;
  is_starred: boolean;
  requires_decryption: boolean;
  decrypt_endpoint: string;
  security_info: {
    level: number;
    algorithm: string;
    quantum_enhanced: boolean;
  };
  encryption_metadata?: any;
}

export interface DecryptedEmail {
  email_id: number;
  subject: string;
  body: string;
  sender_email: string;
  receiver_email: string;
  security_level: number;
  algorithm: string;
  verification_status: string;
  quantum_enhanced: boolean;
  timestamp: string;
  flow_id: string;
  key_id?: string;
  encrypted_size?: number;
  attachments?: Array<{
    filename: string;
    content: string;
    mime_type: string;
    size: number;
  }>;
}

export interface DecryptEmailResponse {
  success: boolean;
  message: string;
  email_data: DecryptedEmail;
  security_info: {
    security_level: number;
    algorithm: string;
    verification_status: string;
    quantum_enhanced: boolean;
    encrypted_size?: number;
  };
}

export interface SendQuantumEmailResponse {
  success: boolean;
  message: string;
  emailId: number;
  emailUuid?: string;
  flowId: string;
  gmailMessageId?: string;
  gmailThreadId?: string;
  encryptionMethod: string;
  securityLevel: number;
  entropy?: number;
  keyId?: string;
  encryptedSize: number;
  timestamp: string;
  sent_via_gmail: boolean;
  viewInOtherApps?: string;
  viewInQuMail?: string;
  encryption_details?: any;
}

export interface EncryptionStatus {
  system_status: string;
  security_levels: Record<number, {
    name: string;
    available: boolean;
    algorithm: string;
    quantum_enhanced: boolean;
    error?: string;
  }>;
  quantum_availability: boolean;
  timestamp: string;
}

class EmailService {
  // Local cache key prefix (for localStorage fallback)
  private readonly CACHE_PREFIX = 'qumail_email_';
  
  /**
   * Get cached decrypted email - tries SQLite first, then localStorage
   */
  async getCachedEmailAsync(emailId: string): Promise<DecryptedEmail | null> {
    // Try SQLite in Electron first
    if (offlineService.isElectronApp) {
      const cached = await offlineService.getCachedDecryption(emailId);
      if (cached) {
        console.log(`📦 Retrieved cached email from SQLite: ${emailId}`);
        return {
          email_id: parseInt(emailId) || 0,
          subject: '',
          body: cached.decrypted_body,
          sender_email: '',
          receiver_email: '',
          security_level: cached.security_info?.security_level || 0,
          algorithm: cached.security_info?.algorithm || '',
          verification_status: cached.security_info?.verification_status || 'Verified',
          quantum_enhanced: cached.security_info?.quantum_enhanced || false,
          timestamp: new Date().toISOString(),
          flow_id: emailId,
          ...cached.security_info
        } as DecryptedEmail;
      }
    }
    
    // Fallback to localStorage
    return this.getCachedEmail(emailId);
  }

  /**
   * Get cached decrypted email from localStorage (sync version)
   */
  getCachedEmail(emailId: string): DecryptedEmail | null {
    try {
      const cached = localStorage.getItem(`${this.CACHE_PREFIX}${emailId}`);
      if (cached) {
        const parsed = JSON.parse(cached);
        console.log(`📦 Retrieved cached email from localStorage: ${emailId}`);
        return parsed.email_data;
      }
    } catch (e) {
      console.warn('Failed to get cached email:', e);
    }
    return null;
  }

  /**
   * Cache decrypted email - saves to both SQLite and localStorage
   */
  async cacheEmailAsync(emailId: string, flowId: string | undefined, emailData: DecryptedEmail, securityInfo: any): Promise<void> {
    // Save to SQLite in Electron
    if (offlineService.isElectronApp) {
      await offlineService.cacheDecryption(
        emailId,
        flowId,
        emailData.body,
        undefined, // HTML version if available
        securityInfo
      );
      console.log(`💾 Cached decrypted email to SQLite: ${emailId}`);
    }
    
    // Also save to localStorage as fallback
    this.cacheEmail(emailId, emailData, securityInfo);
  }

  /**
   * Cache decrypted email to localStorage (like Gmail's offline storage)
   */
  cacheEmail(emailId: string, emailData: DecryptedEmail, securityInfo: any): void {
    try {
      localStorage.setItem(`${this.CACHE_PREFIX}${emailId}`, JSON.stringify({
        email_data: emailData,
        security_info: securityInfo,
        cached_at: new Date().toISOString()
      }));
      console.log(`💾 Cached email to localStorage: ${emailId}`);
    } catch (e) {
      console.warn('Failed to cache email:', e);
    }
  }

  /**
   * Check if email is already decrypted in cache (async version)
   */
  async isEmailDecryptedAsync(emailId: string): Promise<boolean> {
    if (offlineService.isElectronApp) {
      const cached = await offlineService.getCachedDecryption(emailId);
      if (cached) return true;
    }
    return this.isEmailDecrypted(emailId);
  }

  /**
   * Check if email is already decrypted in cache
   */
  isEmailDecrypted(emailId: string): boolean {
    return localStorage.getItem(`${this.CACHE_PREFIX}${emailId}`) !== null;
  }

  /**
   * Send quantum-encrypted email
   */
  async sendQuantumEmail(emailData: SendQuantumEmailRequest): Promise<SendQuantumEmailResponse> {
    try {
      const response = await apiClient.post('/api/v1/emails/send/quantum', emailData);
      return response.data;
    } catch (error: any) {
      console.error('Error sending quantum email:', error);
      throw new Error(error.response?.data?.detail || 'Failed to send quantum email');
    }
  }

  /**
   * Decrypt quantum-secured email using direct method (no MongoDB)
   * All metadata comes from Gmail headers
   */
  async decryptEmailDirect(params: {
    ciphertext: string;
    flow_id: string;
    key_id?: string;
    key_fragments?: string[];
    security_level: number;
    algorithm?: string;
    auth_tag?: string;
    nonce?: string;
    salt?: string;
    plaintext_size?: number;
    subject?: string;
    sender_email?: string;
    // Level 3 PQC-specific fields
    kem_ciphertext?: string;
    kem_secret_key?: string;
    kem_public_key?: string;
    dsa_public_key?: string;
    signature?: string;
    quantum_enhancement?: { enabled: boolean; key_ids?: { km1?: string; km2?: string } };
    // Legacy aliases
    kyber_ciphertext?: string;
    kyber_private_key?: string;
    dilithium_public_key?: string;
  }): Promise<DecryptEmailResponse> {
    try {
      // Check SQLite cache first in Electron
      const cachedData = await this.getCachedEmailAsync(params.flow_id);
      if (cachedData) {
        return {
          success: true,
          message: 'Email retrieved from offline cache',
          email_data: cachedData,
          security_info: {
            security_level: cachedData.security_level,
            algorithm: cachedData.algorithm,
            verification_status: cachedData.verification_status || 'Verified',
            quantum_enhanced: cachedData.quantum_enhanced,
            encrypted_size: cachedData.encrypted_size
          }
        };
      }

      const response = await apiClient.post('/api/v1/emails/decrypt-direct', params);
      
      // Cache the decrypted result to SQLite and localStorage
      if (response.data.success) {
        await this.cacheEmailAsync(
          params.flow_id,
          params.flow_id,
          response.data.email_data,
          response.data.security_info
        );
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error decrypting email directly:', error);
      throw new Error(error.response?.data?.detail || 'Failed to decrypt email');
    }
  }

  /**
   * Decrypt quantum-secured email (checks cache first, then tries direct or legacy)
   */
  async decryptEmail(emailId: string | number): Promise<DecryptEmailResponse> {
    const id = String(emailId);
    
    // Check SQLite cache first in Electron, then localStorage
    const cached = await this.getCachedEmailAsync(id);
    if (cached) {
      return {
        success: true,
        message: 'Email retrieved from offline cache',
        email_data: cached,
        security_info: {
          security_level: cached.security_level,
          algorithm: cached.algorithm,
          verification_status: cached.verification_status || 'Verified',
          quantum_enhanced: cached.quantum_enhanced,
          encrypted_size: cached.encrypted_size
        }
      };
    }
    
    // Not cached, call backend
    try {
      const response = await apiClient.post(`/api/v1/emails/email/${id}/decrypt`);
      
      // Cache the result to SQLite and localStorage
      if (response.data.success) {
        await this.cacheEmailAsync(
          id,
          response.data.email_data?.flow_id,
          response.data.email_data,
          response.data.security_info
        );
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error decrypting email:', error);
      throw new Error(error.response?.data?.detail || 'Failed to decrypt email');
    }
  }

  /**
   * Get email details (encrypted content only)
   */
  async getEmailDetails(emailId: string | number): Promise<QuantumEmail> {
    try {
      const response = await apiClient.get(`/api/v1/emails/email/${emailId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error getting email details:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get email details');
    }
  }

  /**
   * Get list of emails in folder
   */
  async getEmails(folder: string, pageToken?: string, maxResults?: number): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (pageToken) params.append('page_token', pageToken);
      if (maxResults) params.append('max_results', maxResults.toString());
      
      const response = await apiClient.get(`/api/v1/emails/${folder}?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      console.error('Error getting emails:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get emails');
    }
  }

  /**
   * Get encryption system status
   */
  async getEncryptionStatus(): Promise<EncryptionStatus> {
    try {
      const response = await apiClient.get('/api/v1/emails/encryption/status');
      return response.data;
    } catch (error: any) {
      console.error('Error getting encryption status:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get encryption status');
    }
  }

  /**
   * Get email folders
   */
  async getEmailFolders(): Promise<any[]> {
    try {
      const response = await apiClient.get('/api/v1/emails/folders');
      return response.data;
    } catch (error: any) {
      console.error('Error getting email folders:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get email folders');
    }
  }

  /**
   * Mark email as read/unread
   */
  async markEmailAsRead(emailId: number, isRead: boolean = true): Promise<void> {
    try {
      await apiClient.patch(`/api/v1/emails/email/${emailId}`, {
        is_read: isRead
      });
    } catch (error: any) {
      console.error('Error marking email as read:', error);
      throw new Error(error.response?.data?.detail || 'Failed to update email status');
    }
  }

  /**
   * Star/unstar email
   */
  async starEmail(emailId: number, isStarred: boolean = true): Promise<void> {
    try {
      await apiClient.patch(`/api/v1/emails/email/${emailId}`, {
        is_starred: isStarred
      });
    } catch (error: any) {
      console.error('Error starring email:', error);
      throw new Error(error.response?.data?.detail || 'Failed to update email status');
    }
  }
}

export const emailService = new EmailService();
export default emailService;
