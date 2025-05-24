// hercules/frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
// Using the mock client
import { supabase, SupabaseClient } from '../lib/supabaseClientMock'; 
import axios from 'axios'; // For calling backend

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AuthContextType {
  supabaseClient: SupabaseClient; // Mock client type
  session: any | null; // Mock session type
  user: any | null;    // Mock user type
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<any | null>(null);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true); // For initial session check

  useEffect(() => {
    // Simulate checking for an existing session (e.g., from localStorage)
    const checkSession = async () => {
      setLoading(true);
      const storedToken = localStorage.getItem('hercules_auth_token');
      if (storedToken) {
        try {
          // In a real app with Supabase, you might validate token or get session
          // For mock, just assume token is valid if present & simulate user/session
          // This part would be more complex with real supabase.auth.getSession()
          // and onAuthStateChange
          const mockStoredUser = JSON.parse(localStorage.getItem('hercules_user_info') || '{}');
          if (mockStoredUser.id) {
             setSession({ access_token: storedToken, user: mockStoredUser });
             setUser(mockStoredUser);
          } else {
             localStorage.removeItem('hercules_auth_token');
             localStorage.removeItem('hercules_user_info');
          }
        } catch (error) {
          console.error("Error parsing stored user info", error);
          localStorage.removeItem('hercules_auth_token');
          localStorage.removeItem('hercules_user_info');
        }
      }
      setLoading(false);
    };
    checkSession();

    // Mock onAuthStateChange - not fully implemented here, real Supabase handles this.
    // const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
    //   setSession(session);
    //   setUser(session?.user ?? null);
    //   setLoading(false);
    // });
    // return () => subscription?.unsubscribe();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/auth/login`, { email, password });
      const { access_token, user_id, email: userEmail } = response.data;
      
      const mockCurrentSession = { access_token, token_type: 'bearer', user: { id: user_id, email: userEmail } };
      setSession(mockCurrentSession);
      setUser(mockCurrentSession.user);
      localStorage.setItem('hercules_auth_token', access_token);
      localStorage.setItem('hercules_user_info', JSON.stringify(mockCurrentSession.user));

    } catch (error: any) {
      console.error('Login error:', error.response?.data?.detail || error.message);
      throw error.response?.data || new Error("Login failed");
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/auth/register`, { email, password });
      const { access_token, user_id, email: userEmail } = response.data;

      const mockCurrentSession = { access_token, token_type: 'bearer', user: { id: user_id, email: userEmail } };
      setSession(mockCurrentSession);
      setUser(mockCurrentSession.user);
      localStorage.setItem('hercules_auth_token', access_token);
      localStorage.setItem('hercules_user_info', JSON.stringify(mockCurrentSession.user));

    } catch (error: any) {
      console.error('Registration error:', error.response?.data?.detail || error.message);
      throw error.response?.data || new Error("Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    // With real Supabase: await supabase.auth.signOut();
    // For mock and backend token invalidation (if any):
    // await axios.post(`${API_URL}/auth/logout`, {}, { headers: { Authorization: `Bearer ${session?.access_token}` } });
    // For now, just clear client side
    setSession(null);
    setUser(null);
    localStorage.removeItem('hercules_auth_token');
    localStorage.removeItem('hercules_user_info');
    setLoading(false);
    console.log("User logged out (mock)");
  };

  return (
    <AuthContext.Provider value={{ supabaseClient: supabase, session, user, loading, login, register, logout }}>
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
