import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { User, AuthState } from '../types';

interface AuthStore extends AuthState {
  sessionToken: string | null;
  sessionExpiry: string | null;
  login: (user: User, sessionToken: string, expiresAt?: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  updateUser: (user: Partial<User>) => void;
  isSessionValid: () => boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      sessionToken: null,
      sessionExpiry: null,
      isLoading: false,
      
      login: (user: User, sessionToken: string, expiresAt?: string) => {
        set({
          isAuthenticated: true,
          user,
          accessToken: sessionToken, // Keep for backward compatibility
          sessionToken,
          sessionExpiry: expiresAt || null,
          isLoading: false,
        });
      },
      
      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          accessToken: null,
          sessionToken: null,
          sessionExpiry: null,
          isLoading: false,
        });
      },
      
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
      
      updateUser: (userData: Partial<User>) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }));
      },

      isSessionValid: () => {
        const { sessionToken, sessionExpiry } = get();
        if (!sessionToken) return false;
        if (!sessionExpiry) return true; // No expiry set, assume valid
        return new Date(sessionExpiry) > new Date();
      },
    }),
    {
      name: 'qumail-auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        accessToken: state.accessToken,
        sessionToken: state.sessionToken,
        sessionExpiry: state.sessionExpiry,
      }),
    }
  )
);
