import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Animated, { FadeInDown, ZoomIn } from 'react-native-reanimated';

import { useTheme } from '../../constants/theme';
import { useNotificationStore, AppNotification } from '../../store/notificationStore';
import { approveJoinRequest, rejectJoinRequest } from '../../app/api/client';

function NotificationItem({
  item,
  index,
  theme,
  router,
}: {
  item: AppNotification;
  index: number;
  theme: any;
  router: any;
}) {
  const markAsRead = useNotificationStore((state) => state.markAsRead);
  const [actionTaken, setActionTaken] = useState<'approved' | 'rejected' | null>(
    item.type === 'community_join_request' &&
    item.extra_data?.request_status &&
    item.extra_data.request_status !== 'pending'
      ? item.extra_data.request_status
      : null
  );

  const handlePress = () => {
    if (!item.is_read) {
      markAsRead(item.id);
    }
    // Navigate based on type
    if (item.type === 'community_join_request' || item.type === 'community_approved') {
      if (item.entity_id) {
        router.push(`/community/${item.entity_id}`);
      }
    }
  };

  const handleApprove = async () => {
    if (!item.entity_id || !item.actor?.id) return;
    try {
      await approveJoinRequest(item.entity_id, item.actor.id);
      if (!item.is_read) markAsRead(item.id);
      setActionTaken('approved');
    } catch (e) {
      console.error(e);
      Alert.alert('Error', 'This request is no longer valid or has already been processed.');
      setActionTaken('rejected');
    }
  };

  const handleReject = async () => {
    if (!item.entity_id || !item.actor?.id) return;
    try {
      await rejectJoinRequest(item.entity_id, item.actor.id);
      if (!item.is_read) markAsRead(item.id);
      setActionTaken('rejected');
    } catch (e) {
      console.error(e);
      Alert.alert('Error', 'This request is no longer valid or has already been processed.');
      setActionTaken('rejected');
    }
  };

  const renderIcon = () => {
    let iconName = 'notifications';
    let color = theme.accent;

    if (item.type === 'community_join_request') {
      iconName = 'person-add';
      color = theme.warning || '#F59E0B';
    } else if (item.type === 'community_approved') {
      iconName = 'checkmark-circle';
      color = theme.success;
    } else if (item.type === 'community_rejected') {
      iconName = 'close-circle';
      color = theme.error;
    }

    return (
      <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
        <Ionicons name={iconName as any} size={24} color={color} />
      </View>
    );
  };

  return (
    <Animated.View entering={FadeInDown.delay(index * 50).duration(400)}>
      <TouchableOpacity
        style={[
          styles.card,
          {
            backgroundColor: item.is_read ? theme.bgCard : theme.bgSubtle,
            borderColor: theme.border,
          },
        ]}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        <View style={styles.cardHeader}>
          {renderIcon()}
          <View style={styles.textContent}>
            <Text style={[styles.title, { color: theme.textPrimary }]}>
              {item.title}
            </Text>
            <Text style={[styles.body, { color: theme.textSecondary }]}>
              {item.body}
            </Text>
            <Text style={[styles.time, { color: theme.textMuted }]}>
              {new Date(item.created_at).toLocaleString()}
            </Text>
          </View>
          {!item.is_read && (
            <View style={[styles.unreadDot, { backgroundColor: theme.accent }]} />
          )}
        </View>

        {item.type === 'community_join_request' && !actionTaken && (
          <View style={styles.actionRow}>
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: theme.error + '20' }]}
              onPress={handleReject}
            >
              <Text style={[styles.actionText, { color: theme.error }]}>Reject</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: theme.success + '20' }]}
              onPress={handleApprove}
            >
              <Text style={[styles.actionText, { color: theme.success }]}>Approve</Text>
            </TouchableOpacity>
          </View>
        )}
        {item.type === 'community_join_request' && actionTaken && (
          <View style={styles.actionRow}>
            <View
              style={[
                styles.actionBtn,
                { backgroundColor: actionTaken === 'approved' ? theme.success + '20' : theme.error + '20' },
              ]}
            >
              <Text
                style={[
                  styles.actionText,
                  { color: actionTaken === 'approved' ? theme.success : theme.error },
                ]}
              >
                {actionTaken === 'approved' ? 'Approved' : 'Rejected'}
              </Text>
            </View>
          </View>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
}

export default function NotificationsScreen() {
  const theme = useTheme();
  const router = useRouter();

  const notifications = useNotificationStore((state) => state.notifications);
  const loading = useNotificationStore((state) => state.loading);
  const hasMore = useNotificationStore((state) => state.hasMore);
  const fetchInitial = useNotificationStore((state) => state.fetchInitial);
  const fetchMore = useNotificationStore((state) => state.fetchMore);
  const markAllAsRead = useNotificationStore((state) => state.markAllAsRead);

  useEffect(() => {
    fetchInitial();
  }, []);

  return (
    <View style={[styles.root, { backgroundColor: theme.bg }]}>
      <Animated.View
        entering={FadeInDown.duration(500)}
        style={[
          styles.header,
          { backgroundColor: theme.bgCard, borderBottomColor: theme.border },
        ]}
      >
        <View style={styles.headerLeft}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={theme.textPrimary} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.textPrimary }]}>
            Notifications
          </Text>
        </View>
        <TouchableOpacity onPress={() => markAllAsRead()} style={styles.markAllBtn}>
          <Ionicons name="checkmark-done" size={20} color={theme.accent} />
        </TouchableOpacity>
      </Animated.View>

      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        renderItem={({ item, index }) => (
          <NotificationItem item={item} index={index} theme={theme} router={router} />
        )}
        contentContainerStyle={{ padding: 16 }}
        showsVerticalScrollIndicator={false}
        onEndReached={() => fetchMore()}
        onEndReachedThreshold={0.5}
        ListFooterComponent={
          loading && hasMore ? (
            <ActivityIndicator size="small" color={theme.accent} style={{ padding: 20 }} />
          ) : null
        }
        ListEmptyComponent={
          !loading ? (
            <View style={styles.empty}>
              <Ionicons name="notifications-off-outline" size={64} color={theme.textMuted} />
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                No notifications yet.
              </Text>
            </View>
          ) : (
            <ActivityIndicator size="large" color={theme.accent} style={{ marginTop: 40 }} />
          )
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 56 : 40,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  backBtn: { padding: 4 },
  headerTitle: { fontSize: 20, fontWeight: '700' },
  markAllBtn: { padding: 4 },
  card: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textContent: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  body: {
    fontSize: 14,
    marginBottom: 6,
  },
  time: {
    fontSize: 12,
  },
  unreadDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginTop: 6,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#00000010', // Or theme.border
    paddingTop: 12,
  },
  actionBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  actionText: {
    fontWeight: '600',
    fontSize: 14,
  },
  empty: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
  },
});
