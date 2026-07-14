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
  follower_count: number;
  following_count: number;
}

interface AuthState {
  user: User | null;
  token: string | null; // ← Bug #2 fix: exposed for background task access
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (access_token: string, refresh_token: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
  incrementFollowing: () => void;
  decrementFollowing: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (access_token, refresh_token, user) => {
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('refresh_token', refresh_token);
    set({ user, token: access_token, isAuthenticated: true, isLoading: false });
  },

  logout: async () => {
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
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        set({ user: null, token: null, isAuthenticated: false, isLoading: false });
        return;
      }
      const response = await apiClient.get('/auth/me');
      if (response.data.success) {
        set({ user: response.data.data, token, isAuthenticated: true, isLoading: false });
      } else {
        throw new Error('Failed to fetch profile');
      }
    } catch (error) {
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user) => set({ user }),

  incrementFollowing: () => set((state) => ({
    user: state.user ? { ...state.user, following_count: (state.user.following_count || 0) + 1 } : null
  })),

  decrementFollowing: () => set((state) => ({
    user: state.user ? { ...state.user, following_count: Math.max(0, (state.user.following_count || 0) - 1) } : null
  })),
}));
