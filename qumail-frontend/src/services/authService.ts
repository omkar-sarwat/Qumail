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
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Don't try to refresh or redirect if offline
    if (!navigator.onLine || error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.log('[AuthService] Network error while offline - not logging out');
      return Promise.reject(error);
    }
    
    // If error is 401 and we haven't tried refreshing yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        const response = await apiClient.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        });
        
        const { access_token } = response.data;
        
        // Update stored token
        localStorage.setItem('authToken', access_token);
        
        // Update auth header
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        
        // Retry original request
        return apiClient(originalRequest);
      } catch (refreshError: any) {
        // Don't redirect if offline
        if (!navigator.onLine || refreshError.code === 'ERR_NETWORK' || refreshError.message === 'Network Error') {
          console.log('[AuthService] Refresh failed while offline - keeping auth state');
          return Promise.reject(refreshError);
        }
        
        // If refresh fails, clear auth and redirect to login
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        window.location.href = '/';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export interface GoogleAuthResponse {
  authorization_url: string;
  state: string;
}

export interface AuthCallbackResponse {
  success: boolean;
  session_token: string;
  user_email: string;
  user_name?: string;
  picture?: string;
  expires_at: string;
  refresh_token: string;
}

export interface User {
  email: string;
  name?: string;
  picture?: string;
}

class AuthService {
  /**
   * Start Google OAuth flow
   */
  async startGoogleAuth(): Promise<GoogleAuthResponse> {
    try {
      // Detect if running in Electron
      const isElectron = !!(window as any).electronAPI
      const params: any = { is_electron: isElectron }
      
      const response = await apiClient.get('/api/v1/auth/google', {
        params
      });
      return response.data;
    } catch (error: any) {
      console.error('Failed to start Google auth:', error);
      throw new Error(error.response?.data?.detail || 'Failed to start authentication');
    }
  }

  /**
   * Handle OAuth callback
   */
  async handleCallback(code: string, state: string): Promise<AuthCallbackResponse> {
    try {
      const response = await apiClient.post('/api/v1/auth/callback', {
        code,
        state
      });

      const { session_token, refresh_token, user_email, user_name, picture } = response.data;

      // Store tokens and user info
      localStorage.setItem('authToken', session_token);
      localStorage.setItem('refreshToken', refresh_token);
      localStorage.setItem('user', JSON.stringify({
        email: user_email,
        name: user_name || user_email.split('@')[0],
        picture: picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user_email.split('@')[0])}&background=6366f1&color=fff`
      }));

      return response.data;
    } catch (error: any) {
      console.error('OAuth callback failed:', error);
      throw new Error(error.response?.data?.detail || 'Authentication failed');
    }
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiClient.get('/api/v1/auth/me');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get user info:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get user info');
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of server response
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('authToken');
  }

  /**
   * Get stored auth token
   */
  getToken(): string | null {
    return localStorage.getItem('authToken');
  }

  /**
   * Get stored user info
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
}

export const authService = new AuthService();
export default authService;