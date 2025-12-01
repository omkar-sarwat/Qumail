import React, { createContext, useContext, useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { authService, User } from '../services/authService';

// Helper to get auth from Zustand's localStorage if authService doesn't have it
const getZustandAuth = (): { user: User | null; token: string | null } => {
  const zustandAuth = localStorage.getItem('qumail-auth');
  if (!zustandAuth) return { user: null, token: null };
  
  try {
    const parsed = JSON.parse(zustandAuth);
    const state = parsed?.state;
    if (!state) return { user: null, token: null };
    
    const token = state.sessionToken || null;
    const zustandUser = state.user;
    
    // Convert Zustand user format to authService User format
    const user: User | null = zustandUser ? {
      email: zustandUser.email,
      name: zustandUser.displayName || zustandUser.email?.split('@')[0],
      picture: `https://ui-avatars.com/api/?name=${encodeURIComponent(zustandUser.displayName || zustandUser.email?.split('@')[0] || 'U')}&background=6366f1&color=fff`
    } : null;
    
    return { user, token };
  } catch (e) {
    console.warn('[Auth] Failed to parse qumail-auth:', e);
    return { user: null, token: null };
  }
};

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const initStarted = useRef(false);

  // Initialize auth state from local storage - only once
  useEffect(() => {
    // Prevent double initialization
    if (initStarted.current) return;
    initStarted.current = true;

    const initAuth = async () => {
      try {
        // First try the main authService storage
        let storedUser = authService.getStoredUser();
        let storedToken = authService.getToken();
        
        // If not found, try Zustand's persisted storage as fallback
        if (!storedUser || !storedToken) {
          console.log('🔍 [Auth] No authService credentials, checking Zustand storage...');
          const zustandAuth = getZustandAuth();
          if (zustandAuth.user && zustandAuth.token) {
            console.log('✅ [Auth] Found credentials in Zustand storage - syncing');
            storedUser = zustandAuth.user;
            storedToken = zustandAuth.token;
            
            // Sync back to authService storage
            localStorage.setItem('authToken', storedToken);
            localStorage.setItem('user', JSON.stringify(storedUser));
          }
        }
        
        // Check if we have stored credentials
        if (storedUser && storedToken) {
          // ALWAYS set the user first so the app doesn't show login screen
          console.log('👤 [Auth] Setting user from storage:', storedUser.email);
          setUser(storedUser);
          
          // If offline, we're done - just use cached credentials
          if (!navigator.onLine) {
            console.log('📴 [Auth] Offline mode - using cached credentials');
            setIsLoading(false);
            return;
          }
          
          // If online, verify token is still valid in the background
          console.log('🌐 [Auth] Online mode - verifying credentials with server');
          try {
            const freshUser = await authService.getCurrentUser();
            setUser(freshUser); // Update with fresh data if available
            console.log('✅ [Auth] Credentials verified successfully');
          } catch (fetchError: any) {
            console.error('⚠️ [Auth] Failed to verify credentials:', fetchError);
            
            // If network error, keep using cached user
            if (fetchError.code === 'ERR_NETWORK' || fetchError.message === 'Network Error' || !navigator.onLine) {
              console.log('📴 [Auth] Network error - keeping cached user');
              // User is already set, just continue
            } else if (fetchError.response?.status === 401) {
              // Token is actually invalid (not just network issue)
              console.log('🔒 [Auth] Token expired - clearing credentials');
              await authService.logout();
              setUser(null);
            } else {
              // Other errors - keep cached user for now
              console.log('⚠️ [Auth] Unknown error - keeping cached user');
            }
          }
        } else {
          console.log('❌ [Auth] No stored credentials found');
          setUser(null);
        }
      } catch (error) {
        console.error('💥 [Auth] Failed to initialize auth:', error);
        // Only clear auth if we're online and got a real error
        if (navigator.onLine) {
          await authService.logout();
          setUser(null);
        } else {
          // If offline and error, try to use any stored user
          const storedUser = authService.getStoredUser();
          if (storedUser) {
            console.log('📴 [Auth] Error but offline - using cached user');
            setUser(storedUser);
          }
        }
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.startGoogleAuth();
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    // Don't try to refresh if offline
    if (!navigator.onLine) {
      console.log('[Auth] Offline - skipping user refresh');
      return;
    }
    
    try {
      const freshUser = await authService.getCurrentUser();
      setUser(freshUser);
    } catch (error: any) {
      console.error('Failed to refresh user:', error);
      // Only logout on 401 if we're online
      if (navigator.onLine && error instanceof Error && error.message.includes('401')) {
        // Token expired or invalid
        await logout();
      }
    }
  }, [logout]);

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo(() => ({
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  }), [user, isLoading, login, logout, refreshUser]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthProvider;