import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
   * Decrypt quantum-secured email
   */
  async decryptEmail(emailId: string | number): Promise<DecryptEmailResponse> {
    try {
      const response = await apiClient.post(`/api/v1/emails/email/${String(emailId)}/decrypt`);
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
