/**
 * Decrypt Authentication Service
 * 
 * Handles Google Authenticator TOTP verification for email decryption.
 * 
 * Flow:
 * 1. First decrypt - Uses quantum keys (KME)
 * 2. Subsequent decrypts - Requires TOTP code from Google Authenticator
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://qumail-backend-gwec.onrender.com';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============================================
// Types
// ============================================

export interface DecryptAuthStatus {
  totp_setup: boolean;
  totp_verified: boolean;
  user_email: string;
}

export interface Setup2FAResponse {
  qr_code: string;  // Base64 PNG image
  secret: string;   // Manual entry secret
  message: string;
  already_setup: boolean;
}

export interface Verify2FASetupResponse {
  success: boolean;
  message: string;
}

export interface VerifyDecryptTOTPResponse {
  success: boolean;
  message: string;
  valid_until?: string;
}

// ============================================
// Local Storage Keys
// ============================================

const STORAGE_KEYS = {
  // Track which emails have been decrypted with quantum keys (first time)
  FIRST_DECRYPT_PREFIX: 'qumail_first_decrypt_',
  // Track TOTP verification sessions (per email)
  TOTP_SESSION_PREFIX: 'qumail_totp_session_',
  // Global TOTP session (for any email within 5 min)
  TOTP_GLOBAL_SESSION: 'qumail_totp_global_session',
};

// ============================================
// Service Class
// ============================================

class DecryptAuthService {
  /**
   * Check if TOTP is set up for the current user
   */
  async getStatus(): Promise<DecryptAuthStatus> {
    try {
      const response = await apiClient.get('/api/v1/decrypt-auth/status');
      return response.data;
    } catch (error: any) {
      console.error('Error checking decrypt auth status:', error);
      throw new Error(error.response?.data?.detail || 'Failed to check TOTP status');
    }
  }

  /**
   * Set up Google Authenticator for decrypt verification
   * Returns QR code to scan
   */
  async setup2FA(): Promise<Setup2FAResponse> {
    try {
      const response = await apiClient.post('/api/v1/decrypt-auth/setup');
      return response.data;
    } catch (error: any) {
      console.error('Error setting up 2FA:', error);
      throw new Error(error.response?.data?.detail || 'Failed to set up Google Authenticator');
    }
  }

  /**
   * Verify initial 2FA setup with a code from Google Authenticator
   */
  async verifySetup(code: string): Promise<Verify2FASetupResponse> {
    try {
      const response = await apiClient.post('/api/v1/decrypt-auth/verify-setup', { code });
      return response.data;
    } catch (error: any) {
      console.error('Error verifying 2FA setup:', error);
      throw new Error(error.response?.data?.detail || 'Invalid code');
    }
  }

  /**
   * Verify TOTP code for accessing a previously decrypted email
   */
  async verifyDecryptTOTP(code: string, emailId: string): Promise<VerifyDecryptTOTPResponse> {
    try {
      const response = await apiClient.post('/api/v1/decrypt-auth/verify-decrypt', {
        code,
        email_id: emailId
      });
      
      // Store successful verification
      if (response.data.success) {
        this.storeVerificationSession(emailId);
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error verifying TOTP for decrypt:', error);
      throw new Error(error.response?.data?.detail || 'Invalid code');
    }
  }

  /**
   * Disable Google Authenticator for decrypt operations
   */
  async disable2FA(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.delete('/api/v1/decrypt-auth/disable');
      return response.data;
    } catch (error: any) {
      console.error('Error disabling 2FA:', error);
      throw new Error(error.response?.data?.detail || 'Failed to disable');
    }
  }

  // ============================================
  // Local State Management
  // ============================================

  /**
   * Check if this is the first time decrypting an email
   * (needs quantum keys vs needs TOTP)
   */
  isFirstDecrypt(emailId: string): boolean {
    const key = `${STORAGE_KEYS.FIRST_DECRYPT_PREFIX}${emailId}`;
    return localStorage.getItem(key) === null;
  }

  /**
   * Mark an email as having been decrypted for the first time
   * Subsequent decrypts will require TOTP
   */
  markFirstDecryptComplete(emailId: string): void {
    const key = `${STORAGE_KEYS.FIRST_DECRYPT_PREFIX}${emailId}`;
    localStorage.setItem(key, JSON.stringify({
      decrypted_at: new Date().toISOString()
    }));
    console.log(`🔑 First decrypt complete for email: ${emailId}`);
  }

  /**
   * Check if user has a valid TOTP session for an email
   * (verified within last 5 minutes)
   * Checks both per-email session AND global session
   */
  hasValidTOTPSession(emailId: string): boolean {
    try {
      const now = new Date();
      
      // Check per-email session first
      const emailSession = localStorage.getItem(`${STORAGE_KEYS.TOTP_SESSION_PREFIX}${emailId}`);
      if (emailSession) {
        const parsed = JSON.parse(emailSession);
        const verifiedAt = new Date(parsed.verified_at);
        const diffMinutes = (now.getTime() - verifiedAt.getTime()) / (1000 * 60);
        if (diffMinutes < 5) {
          return true;
        }
      }
      
      // Check global session (any TOTP verified in last 5 min)
      const globalSession = localStorage.getItem(STORAGE_KEYS.TOTP_GLOBAL_SESSION);
      if (globalSession) {
        const parsed = JSON.parse(globalSession);
        const verifiedAt = new Date(parsed.verified_at);
        const diffMinutes = (now.getTime() - verifiedAt.getTime()) / (1000 * 60);
        if (diffMinutes < 5) {
          return true;
        }
      }
      
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Store a successful TOTP verification session
   * Stores both per-email and global session for flexible checking
   */
  storeVerificationSession(emailId: string): void {
    const sessionData = {
      email_id: emailId,
      verified_at: new Date().toISOString()
    };
    
    // Store per-email session
    localStorage.setItem(`${STORAGE_KEYS.TOTP_SESSION_PREFIX}${emailId}`, JSON.stringify(sessionData));
    
    // Store global session (any TOTP verification grants 5-min access to all decrypted emails)
    localStorage.setItem(STORAGE_KEYS.TOTP_GLOBAL_SESSION, JSON.stringify(sessionData));
    
    console.log(`✅ TOTP session stored for email: ${emailId}`);
  }

  /**
   * Clear all first-decrypt markers (for testing/reset)
   */
  clearAllFirstDecryptMarkers(): void {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(STORAGE_KEYS.FIRST_DECRYPT_PREFIX)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    console.log(`🧹 Cleared ${keysToRemove.length} first-decrypt markers`);
  }
}

export const decryptAuthService = new DecryptAuthService();
export default decryptAuthService;
