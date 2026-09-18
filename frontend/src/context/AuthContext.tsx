'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, AuthUser, AuthResponse } from '@/lib/api';

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signUp: (email: string, password: string, name?: string) => Promise<{ success: boolean; error?: string }>;
  demoAccess: () => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'irrigation_auth_token';
const USER_KEY = 'irrigation_auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  // Initialize session from local storage and verify with backend
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (typeof window !== 'undefined') {
          const storedToken = localStorage.getItem(TOKEN_KEY);
          const storedUser = localStorage.getItem(USER_KEY);

          if (storedToken && storedUser) {
            setToken(storedToken);
            try {
              setUser(JSON.parse(storedUser));
            } catch {
              // Ignore parse error
            }

            // Verify token validity with backend
            try {
              const res = await api.getMe();
              if (res && res.user) {
                setUser(res.user);
                localStorage.setItem(USER_KEY, JSON.stringify(res.user));
              }
            } catch {
              // If token expired or invalid, clear session and open login dialog
              localStorage.removeItem(TOKEN_KEY);
              localStorage.removeItem(USER_KEY);
              setToken(null);
              setUser(null);
              setIsAuthModalOpen(true);
            }
          } else {
            // First time accessing the site unauthenticated: open login dialog
            setIsAuthModalOpen(true);
          }
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const openAuthModal = useCallback(() => setIsAuthModalOpen(true), []);
  const closeAuthModal = useCallback(() => setIsAuthModalOpen(false), []);

  const login = useCallback(async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    try {
      const res = await api.login(email, password);
      if (res && res.token) {
        setToken(res.token);
        setUser(res.user);
        setIsAuthModalOpen(false);
        if (typeof window !== 'undefined') {
          localStorage.setItem(TOKEN_KEY, res.token);
          localStorage.setItem(USER_KEY, JSON.stringify(res.user));
        }
        return { success: true };
      }
      return { success: false, error: 'Failed to authenticate operator.' };
    } catch (err: any) {
      return { success: false, error: err.message || 'Authentication error. Check your credentials.' };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signUp = useCallback(async (email: string, password: string, name?: string): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    try {
      const res = await api.signUp(email, password, name);
      if (res && res.token) {
        setToken(res.token);
        setUser(res.user);
        setIsAuthModalOpen(false);
        if (typeof window !== 'undefined') {
          localStorage.setItem(TOKEN_KEY, res.token);
          localStorage.setItem(USER_KEY, JSON.stringify(res.user));
        }
        return { success: true };
      }
      return { success: false, error: 'Registration failed.' };
    } catch (err: any) {
      return { success: false, error: err.message || 'Registration error.' };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const demoAccess = useCallback(() => {
    const demoUser: AuthUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'operator@fuzzy-irrigation.local',
      name: 'Demo System Operator',
      role: 'admin',
    };
    const demoToken = 'demo-session-token-local';
    setUser(demoUser);
    setToken(demoToken);
    setIsAuthModalOpen(false);
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, demoToken);
      localStorage.setItem(USER_KEY, JSON.stringify(demoUser));
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // Continue client cleanup even if API fails
    } finally {
      setUser(null);
      setToken(null);
      setIsAuthModalOpen(true);
      if (typeof window !== 'undefined') {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user && !!token,
        isAuthModalOpen,
        openAuthModal,
        closeAuthModal,
        login,
        signUp,
        demoAccess,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
