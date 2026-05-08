/**
 * Authentication Context Provider.
 * Manages global auth state, tokens, and API interactions.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// API base URL - Django backend
const API_URL = 'http://localhost:8000/api/auth';

// Create axios instance with interceptors
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // LOG: outgoing request
  console.log(`[AUTH_API] ${config.method?.toUpperCase()} ${config.url}`, config.data || '');
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => {
    // LOG: successful response
    console.log(`[AUTH_API] ✅ ${response.config.url} →`, response.status, response.data);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    // LOG: error response
    console.error(`[AUTH_API] ❌ ${originalRequest?.url} →`, error.response?.status, error.response?.data);
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_URL}/token/refresh/`, {
          refresh: refreshToken,
        });
        
        const { access } = response.data;
        localStorage.setItem('access_token', access);
        
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Types
interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  is_email_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<{ email: string }>;
  verifyEmail: (email: string, otp_code: string) => Promise<void>;
  resendOTP: (email: string) => Promise<void>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (data: ResetPasswordData) => Promise<void>;
  updatePassword: (data: UpdatePasswordData) => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

interface RegisterData {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
  profile_image?: File;
}

interface ResetPasswordData {
  email: string;
  otp_code: string;
  new_password: string;
  new_password_confirm: string;
}

interface UpdatePasswordData {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    console.log('[AUTH_FLOW] AuthProvider mounted, checking token...');
    const token = localStorage.getItem('access_token');
    console.log('[AUTH_FLOW] Token exists?', !!token);
    if (token) {
      fetchProfile();
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      console.log('[AUTH_FLOW] Fetching profile...');
      const response = await api.get('/profile/');
      console.log('[AUTH_FLOW] Profile fetched:', response.data);
      setUser(response.data);
    } catch (error) {
      console.error('[AUTH_FLOW] Failed to fetch profile:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    console.log('[AUTH_FLOW] Attempting login for:', email);
    const response = await api.post('/login/', { email, password });
    console.log('[AUTH_FLOW] Login response:', response.data);
    const { tokens, user: userData } = response.data;
    
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    setUser(userData);
    console.log('[AUTH_FLOW] Login successful, user set:', userData.email);
  };

  const register = async (data: RegisterData) => {
    console.log('[AUTH_FLOW] Starting registration for:', data.email);
    // Use FormData for file upload
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value);
      }
    });

    const response = await axios.post(`${API_URL}/register/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    console.log('[AUTH_FLOW] Registration successful:', response.data);
    return { email: response.data.email };
  };

  const verifyEmail = async (email: string, otp_code: string) => {
    console.log('[AUTH_FLOW] Verifying email:', email, 'OTP:', otp_code);
    const response = await api.post('/verify-email/', { email, otp_code });
    console.log('[AUTH_FLOW] Verify-email response:', response.data);
    
    // Handle case where backend returns tokens (auto-login after verify)
    if (response.data.tokens) {
      const { tokens, user: userData } = response.data;
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      setUser(userData);
      console.log('[AUTH_FLOW] Auto-login after verify, tokens stored');
    } else {
      console.log('[AUTH_FLOW] Verify success but no tokens returned');
    }
  };

  const resendOTP = async (email: string) => {
    console.log('[AUTH_FLOW] Resending OTP to:', email);
    await api.post('/resend-otp/', { email });
    console.log('[AUTH_FLOW] OTP resent successfully');
  };

  const logout = async () => {
    console.log('[AUTH_FLOW] Logging out...');
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        await api.post('/logout/', { refresh });
      }
    } catch (error) {
      console.error('[AUTH_FLOW] Logout API error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      console.log('[AUTH_FLOW] Logout complete, redirecting to login');
      window.location.href = '/login';
    }
  };

  const forgotPassword = async (email: string) => {
    console.log('[AUTH_FLOW] Requesting password reset for:', email);
    await api.post('/password-reset/request/', { email });
  };

  const resetPassword = async (data: ResetPasswordData) => {
    console.log('[AUTH_FLOW] Resetting password for:', data.email);
    await api.post('/password-reset/confirm/', data);
  };

  const updatePassword = async (data: UpdatePasswordData) => {
    console.log('[AUTH_FLOW] Updating password');
    const response = await api.put('/password/update/', data);
    const { tokens } = response.data;
    
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
  };

  const updateProfile = async (data: Partial<User>) => {
    console.log('[AUTH_FLOW] Updating profile:', data);
    const response = await api.put('/profile/', data);
    setUser(response.data);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        verifyEmail,
        resendOTP,
        logout,
        forgotPassword,
        resetPassword,
        updatePassword,
        updateProfile,
      }}
    >
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