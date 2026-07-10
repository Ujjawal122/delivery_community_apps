import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import apiClient from "../app/api/client"

export interface User {
  id: string;
  full_name: string;
  email: string;
  avatar?: string | null;
  bio?: string | null;
  company?: string | null;
  vehicle_type?: string | null;
  is_verified: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (access_token: string, refresh_token: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start true while we check async storage

  login: async (access_token, refresh_token, user) => {
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('refresh_token', refresh_token);
    set({ user, isAuthenticated: true, isLoading: false });
  },

  logout: async () => {
    // Optionally call backend logout endpoint here
    try {
      const refresh_token = await AsyncStorage.getItem('refresh_token');
      if (refresh_token) {
        await apiClient.post('/auth/logout', { refresh_token });
      }
    } catch (e) {
      // Ignore errors on logout
    }

    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false, isLoading: false });
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }

      // Fetch user profile
      const response = await apiClient.get('/auth/me');
      if (response.data.success) {
        set({ user: response.data.data, isAuthenticated: true, isLoading: false });
      } else {
        throw new Error('Failed to fetch profile');
      }
    } catch (error) {
      // If error, interceptor might have failed to refresh, or server is down
      // we'll clear tokens just to be safe if it's an auth error
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user) => set({ user }),
}));
