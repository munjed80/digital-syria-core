'use client';

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api, ApiError, clearToken, getStoredToken, storeToken } from './api';
import type { User } from './types';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  initializing: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (full_name: string, email: string, password: string) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);

  const loadProfile = useCallback(async (currentToken: string) => {
    try {
      const profile = await api.me(currentToken);
      setUser(profile);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        clearToken();
        setToken(null);
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    const stored = getStoredToken();
    if (stored) {
      setToken(stored);
      loadProfile(stored).finally(() => setInitializing(false));
    } else {
      setInitializing(false);
    }
  }, [loadProfile]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokenResp = await api.login(email, password);
      storeToken(tokenResp.access_token);
      setToken(tokenResp.access_token);
      const profile = await api.me(tokenResp.access_token);
      setUser(profile);
      return profile;
    },
    [],
  );

  const register = useCallback(
    async (full_name: string, email: string, password: string) => {
      const created = await api.register(full_name, email, password);
      // Auto-login after successful registration.
      const tokenResp = await api.login(email, password);
      storeToken(tokenResp.access_token);
      setToken(tokenResp.access_token);
      setUser(created);
      return created;
    },
    [],
  );

  const logout = useCallback(() => {
    clearToken();
    setToken(null);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    if (!token) return;
    await loadProfile(token);
  }, [token, loadProfile]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, initializing, login, register, logout, refresh }),
    [user, token, initializing, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
