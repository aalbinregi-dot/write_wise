import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth as authApi } from '../api/services';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  course: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login:  (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser]     = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access');
    if (token) {
      authApi.me()
        .then(({ data }) => setUser(data))
        .catch(() => autoLoginGuest())
        .finally(() => setLoading(false));
    } else {
      autoLoginGuest();
    }
  }, []);

  const autoLoginGuest = async () => {
    try {
      const { data } = await authApi.login({ email: 'student@writewise.ai', password: 'Test1234!' });
      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);
      setUser(data.user);
    } catch (e) {
      console.error('Guest login error', e);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login({ email, password });
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setUser(data.user);
  };

  const register = async (formData: any) => {
    const { data } = await authApi.register(formData);
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
};
