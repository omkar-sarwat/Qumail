import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';
const AuthContext = createContext(undefined);
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    // Initialize auth state from local storage
    useEffect(() => {
        const initAuth = async () => {
            try {
                const storedUser = authService.getStoredUser();
                if (storedUser && authService.isAuthenticated()) {
                    // Verify token is still valid by fetching fresh user data
                    const freshUser = await authService.getCurrentUser();
                    setUser(freshUser);
                }
            }
            catch (error) {
                console.error('Failed to initialize auth:', error);
                // Clear invalid auth state
                await authService.logout();
                setUser(null);
            }
            finally {
                setIsLoading(false);
            }
        };
        initAuth();
    }, []);
    const login = async () => {
        setIsLoading(true);
        try {
            await authService.startGoogleAuth();
        }
        catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
        finally {
            setIsLoading(false);
        }
    };
    const logout = async () => {
        setIsLoading(true);
        try {
            await authService.logout();
            setUser(null);
        }
        catch (error) {
            console.error('Logout failed:', error);
        }
        finally {
            setIsLoading(false);
        }
    };
    const refreshUser = async () => {
        try {
            const freshUser = await authService.getCurrentUser();
            setUser(freshUser);
        }
        catch (error) {
            console.error('Failed to refresh user:', error);
            if (error instanceof Error && error.message.includes('401')) {
                // Token expired or invalid
                await logout();
            }
        }
    };
    return (_jsx(AuthContext.Provider, { value: {
            user,
            isAuthenticated: !!user,
            isLoading,
            login,
            logout,
            refreshUser,
        }, children: children }));
};
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
export default AuthProvider;
