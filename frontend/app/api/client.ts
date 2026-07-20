import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ── URL Configuration ─────────────────────────────────────────────────────────
// For Android Emulator:  use 'http://10.0.2.2:8000'
// For Physical Device:   use your PC's local Wi-Fi IP (must be same network)
const BASE_URL = 'http://10.0.2.2:8000';


const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
});

// Request Interceptor: Attach the access token if it exists
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 and refresh tokens
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If the error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem('refresh_token');
        if (!refreshToken) {
          // Reject with the original 401 error instead of throwing a generic Error
          return Promise.reject(error);
        }

        // Call refresh endpoint directly using axios to avoid circular interceptor loops
        const response = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        if (response.data.success) {
          const newAccessToken = response.data.data.access_token;
          const newRefreshToken = response.data.data.refresh_token;

          await AsyncStorage.setItem('access_token', newAccessToken);
          await AsyncStorage.setItem('refresh_token', newRefreshToken);

          // Retry the original request with the new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, log the user out properly to clear all stores
        // We import it dynamically to avoid circular dependencies if any
        import('../../store/authStore').then(({ useAuthStore }) => {
          useAuthStore.getState().logout();
        });
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// --- API Functions ---

// Posts
export const getFeed = async (page: number = 1, limit: number = 20, latitude: number = 0, longitude: number = 0, radius_km: number = 50) => {
  const response = await apiClient.post('/posts/feed', { page, limit, latitude, longitude, radius_km });
  return response.data;
};

export const getPost = async (postId: string) => {
  const response = await apiClient.get(`/posts/${postId}`);
  return response.data;
};

export const votePost = async (postId: string, voteType: number) => {
  const typeStr = voteType === 1 ? 'up' : 'down';
  const response = await apiClient.post(`/posts/${postId}/vote`, { vote_type: typeStr });
  return response.data;
};

export const removeVotePost = async (postId: string) => {
  const response = await apiClient.delete(`/posts/${postId}/vote`);
  return response.data;
};

// Comments
export const getComments = async (postId: string, page: number = 1, limit: number = 50) => {
  const response = await apiClient.get(`/posts/${postId}/comments`, { params: { page, limit } });
  return response.data;
};

export const addComment = async (postId: string, content: string, parentId?: string, repliedToUserId?: string) => {
  const response = await apiClient.post(`/posts/${postId}/comments`, {
    content,
    parent_id: parentId || null,
    replied_to_user_id: repliedToUserId || null,
  });
  return response.data;
};

export const voteComment = async (postId: string, commentId: string, voteType: number) => {
  const typeStr = voteType === 1 ? 'up' : 'down';
  const response = await apiClient.post(`/posts/${postId}/comments/${commentId}/vote`, { vote_type: typeStr });
  return response.data;
};

export const removeVoteComment = async (postId: string, commentId: string) => {
  const response = await apiClient.delete(`/posts/${postId}/comments/${commentId}/vote`);
  return response.data;
};

// Users
export const getProfile = async () => {
  const response = await apiClient.get('/users/me');
  return response.data;
};

export const updateProfile = async (data: any) => {
  const response = await apiClient.patch('/users/me', data);
  return response.data;
};

// Communities
export const getCommunities = async (page: number = 1, limit: number = 20) => {
  const response = await apiClient.get('/communities', { params: { page, limit } });
  return response.data;
};

export const getCommunity = async (communityId: string) => {
  const response = await apiClient.get(`/communities/${communityId}`);
  return response.data;
};

export const createCommunity = async (data: { name: string, about?: string, purpose: string, is_public: boolean }) => {
  const response = await apiClient.post('/communities', data);
  return response.data;
};

export const joinCommunity = async (communityId: string) => {
  const response = await apiClient.post(`/communities/${communityId}/join`);
  return response.data;
};

export const checkCommunityMembership = async (communityId: string) => {
  const response = await apiClient.get(`/communities/${communityId}/membership`);
  return response.data;
};

export const getCommunityPosts = async (communityId: string, page: number = 1, limit: number = 20) => {
  const response = await apiClient.get('/posts', { params: { community_id: communityId, page, limit } });
  return response.data;
};

// Follow & Search
export const searchUsers = async (query: string, limit: number = 20, offset: number = 0) => {
  const response = await apiClient.get('/users/search', { params: { q: query, limit, offset } });
  return response.data;
};

export const getSuggestions = async (limit: number = 20) => {
  const response = await apiClient.get('/users/suggestions', { params: { limit } });
  return response.data;
};

export const followUser = async (userId: string) => {
  const response = await apiClient.post(`/users/${userId}/follow`);
  return response.data;
};

export const unfollowUser = async (userId: string) => {
  const response = await apiClient.delete(`/users/${userId}/follow`);
  return response.data;
};

export const getFollowers = async (userId: string, limit: number = 20, offset: number = 0) => {
  const response = await apiClient.get(`/users/${userId}/followers`, { params: { limit, offset } });
  return response.data;
};

export const getFollowing = async (userId: string, limit: number = 20, offset: number = 0) => {
  const response = await apiClient.get(`/users/${userId}/following`, { params: { limit, offset } });
  return response.data;
};

// Notifications
export const getNotifications = async (page: number = 1, limit: number = 20) => {
  const response = await apiClient.get('/notifications', { params: { page, limit } });
  return response.data;
};

export const getUnreadNotificationCount = async () => {
  const response = await apiClient.get('/notifications/unread-count');
  return response.data;
};

export const markNotificationRead = async (notificationId: string) => {
  const response = await apiClient.patch(`/notifications/${notificationId}/read`);
  return response.data;
};

export const markAllNotificationsRead = async () => {
  const response = await apiClient.post('/notifications/mark-all-read');
  return response.data;
};

// Community Join Requests
export const approveJoinRequest = async (communityId: string, userId: string) => {
  const response = await apiClient.post(`/communities/${communityId}/join-requests/${userId}/approve`);
  return response.data;
};

export const rejectJoinRequest = async (communityId: string, userId: string) => {
  const response = await apiClient.post(`/communities/${communityId}/join-requests/${userId}/reject`);
  return response.data;
};

export default apiClient;
