import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Animated, { FadeInDown, ZoomIn } from 'react-native-reanimated';

import { useTheme } from '../constants/theme';
import ThemeToggle from './ThemeToggle';
import { useNotificationStore } from '../store/notificationStore';
import { useChatStore } from '../store/chatStore';
import { useAuthStore } from '../store/authStore';

interface HeaderProps {
  title: string;
}

export default function Header({ title }: HeaderProps) {
  const theme = useTheme();
  const router = useRouter();

  const unreadNotificationCount = useNotificationStore((state) => state.unreadCount);
  const fetchUnreadCount = useNotificationStore((state) => state.fetchUnreadCount);
  const unreadChatCount = useChatStore((state) => state.unreadChatCount);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      fetchUnreadCount();
    }
  }, [isAuthenticated]);

  return (
    <Animated.View
      entering={FadeInDown.duration(500)}
      style={[
        styles.header,
        { backgroundColor: theme.bgCard, borderBottomColor: theme.border },
      ]}
    >
      <View style={styles.headerLeft}>
        <View style={[styles.logoSmall, { backgroundColor: theme.accent }]}>
          <Feather name="truck" size={16} color="#fff" />
        </View>
        <Text style={[styles.headerTitle, { color: theme.textPrimary }]}>{title}</Text>
      </View>
      <View style={styles.headerRight}>
        <TouchableOpacity
          style={styles.iconButton}
          onPress={() => router.push('/chats')}
        >
          <Ionicons name="chatbubble-ellipses-outline" size={24} color={theme.textPrimary} />
          {unreadChatCount > 0 && (
            <Animated.View entering={ZoomIn} style={styles.badge}>
              <Text style={styles.badgeText}>
                {unreadChatCount > 99 ? '99+' : unreadChatCount}
              </Text>
            </Animated.View>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.iconButton}
          onPress={() => router.push('/notifications')}
        >
          <Ionicons name="notifications-outline" size={24} color={theme.textPrimary} />
          {unreadNotificationCount > 0 && (
            <Animated.View entering={ZoomIn} style={styles.badge}>
              <Text style={styles.badgeText}>
                {unreadNotificationCount > 99 ? '99+' : unreadNotificationCount}
              </Text>
            </Animated.View>
          )}
        </TouchableOpacity>

        <ThemeToggle size={20} />
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 56, // Adjusted for safe area / status bar loosely
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  logoSmall: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5 },
  iconButton: {
    position: 'relative',
    padding: 4,
  },
  badge: {
    position: 'absolute',
    top: -2,
    right: -4,
    backgroundColor: '#EF4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#ffffff', // Will be overridden or assume white for light mode, could use theme.bgCard
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
});
