import { create } from 'zustand';
import {
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '../app/api/client';

export interface NotificationActor {
  id: string;
  full_name: string;
  avatar: string | null;
}

export interface AppNotification {
  id: string;
  title: string;
  body: string;
  type: string;
  entity_id: string | null;
  is_read: boolean;
  created_at: string;
  extra_data?: {
    request_status?: 'pending' | 'approved' | 'rejected';
    [key: string]: any;
  } | null;
  actor: NotificationActor | null;
}

interface NotificationState {
  notifications: AppNotification[];
  unreadCount: number;
  loading: boolean;
  page: number;
  hasMore: boolean;

  fetchInitial: () => Promise<void>;
  fetchMore: () => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  addNotification: (notification: AppNotification) => void;
  updateUnreadCount: (count: number) => void;
  incrementUnreadCount: () => void;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  reset: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  page: 1,
  hasMore: true,

  reset: () => set({
    notifications: [],
    unreadCount: 0,
    loading: false,
    page: 1,
    hasMore: true,
  }),

  fetchInitial: async () => {
    set({ loading: true, page: 1 });
    try {
      const res = await getNotifications(1, 20);
      if (res.success) {
        set({
          notifications: res.data.items,
          hasMore: res.data.items.length === 20,
          loading: false,
        });
      }
    } catch (error) {
      console.error('Failed to fetch notifications', error);
      set({ loading: false });
    }
  },

  fetchMore: async () => {
    const { page, hasMore, loading, notifications } = get();
    if (!hasMore || loading) return;

    set({ loading: true });
    try {
      const nextPage = page + 1;
      const res = await getNotifications(nextPage, 20);
      if (res.success) {
        const newItems = res.data.items.filter(
          (newItem: AppNotification) => !notifications.find((n) => n.id === newItem.id)
        );
        set({
          notifications: [...notifications, ...newItems],
          page: nextPage,
          hasMore: res.data.items.length === 20,
          loading: false,
        });
      }
    } catch (error) {
      console.error('Failed to fetch more notifications', error);
      set({ loading: false });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const res = await getUnreadNotificationCount();
      if (res.success) {
        set({ unreadCount: res.data.unread_count });
      }
    } catch (error) {
      console.error('Failed to fetch unread count', error);
    }
  },

  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
    }));
  },

  updateUnreadCount: (count) => set({ unreadCount: count }),

  incrementUnreadCount: () => set((state) => ({ unreadCount: state.unreadCount + 1 })),

  markAsRead: async (id) => {
    const { notifications, unreadCount } = get();
    const notification = notifications.find((n) => n.id === id);
    
    if (notification && !notification.is_read) {
      // Optimistic update
      set({
        notifications: notifications.map((n) =>
          n.id === id ? { ...n, is_read: true } : n
        ),
        unreadCount: Math.max(0, unreadCount - 1),
      });

      try {
        await markNotificationRead(id);
      } catch (error) {
        console.error('Failed to mark as read', error);
        // Revert on failure
        set({
          notifications: notifications,
          unreadCount,
        });
      }
    }
  },

  markAllAsRead: async () => {
    const { notifications, unreadCount } = get();
    
    // Optimistic update
    set({
      notifications: notifications.map((n) => ({ ...n, is_read: true })),
      unreadCount: 0,
    });

    try {
      await markAllNotificationsRead();
    } catch (error) {
      console.error('Failed to mark all as read', error);
      // Revert on failure
      set({ notifications, unreadCount });
    }
  },
}));
