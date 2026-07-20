import React, { useState, useCallback, useEffect } from 'react';
import { useFocusEffect } from 'expo-router';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  Platform,
} from 'react-native';
import Animated, {
  FadeInRight,
  FadeInDown,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  ZoomIn,
} from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import apiClient from '../api/client';
import { useChatStore, Conversation } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import { useWebSocket } from '../../services/useWebSocket';
import { useTheme } from '../../constants/theme';
import ThemeToggle from '../../components/ThemeToggle';

// ── Pulsing Online Dot ─────────────────────────────────────────────────────────
function OnlineDot() {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  useEffect(() => {
    scale.value = withRepeat(
      withSequence(withTiming(1.6, { duration: 800 }), withTiming(1, { duration: 800 })),
      -1,
      false
    );
    opacity.value = withRepeat(
      withSequence(withTiming(0.3, { duration: 800 }), withTiming(1, { duration: 800 })),
      -1,
      false
    );
  }, []);

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return (
    <View style={styles.onlineDotWrapper}>
      <Animated.View style={[styles.onlinePulse, pulseStyle]} />
      <View style={styles.onlineDotCore} />
    </View>
  );
}

// ── Conversation Item ─────────────────────────────────────────────────────────
function ConversationItem({
  item,
  index,
  currentUser,
  onlineUsers,
  theme,
  router,
}: any) {
  const otherMember = item.members?.find((m: any) => m.user_id !== currentUser?.id);
  const otherUser = otherMember?.user;
  if (!otherUser) return null;

  const isOnline = onlineUsers.has(otherUser.id);
  const lastMsg = item.latest_message?.content || 'No messages yet';
  const date = item.latest_message
    ? new Date(item.latest_message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';
  const authorInitial = (otherUser.full_name || 'U').charAt(0).toUpperCase();

  return (
    <Animated.View entering={FadeInRight.delay(index * 60).duration(400).springify()}>
      <TouchableOpacity
        style={[styles.convItem, { borderBottomColor: theme.separator }]}
        onPress={() => router.push(`/chats/${item.id}`)}
        activeOpacity={0.7}
      >
        {/* Avatar */}
        <View style={styles.avatarContainer}>
          {otherUser.avatar ? (
            <Image source={{ uri: otherUser.avatar }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatarPlaceholder, { backgroundColor: theme.accent + '25' }]}>
              <Text style={[styles.avatarInitial, { color: theme.accent }]}>{authorInitial}</Text>
            </View>
          )}
          {isOnline && <OnlineDot />}
        </View>

        {/* Text */}
        <View style={styles.convInfo}>
          <View style={styles.convTopRow}>
            <Text style={[styles.convName, { color: theme.textPrimary }]} numberOfLines={1}>
              {otherUser.full_name}
            </Text>
            <Text style={[styles.convTime, { color: theme.textMuted }]}>{date}</Text>
          </View>
          <Text style={[styles.convPreview, { color: theme.textSecondary }]} numberOfLines={1}>
            {lastMsg}
          </Text>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
}

export default function ChatsListScreen() {
  const theme = useTheme();
  const router = useRouter();
  const currentUser = useAuthStore((state) => state.user);
  const conversations = useChatStore((state) => state.conversations);
  const setConversations = useChatStore((state) => state.setConversations);
  const onlineUsers = useChatStore((state) => state.onlineUsers);
  const [loading, setLoading] = useState(true);

  useWebSocket();

  useFocusEffect(
    useCallback(() => {
      let isActive = true;

      const fetchConversations = async () => {
        try {
          const res = await apiClient.get('/chat/conversations');
          if (isActive) {
            setConversations(res.data);
          }
        } catch (error) {
          console.error('Failed to load conversations', error);
        } finally {
          if (isActive) {
            setLoading(false);
          }
        }
      };

      fetchConversations();

      return () => {
        isActive = false;
      };
    }, [])
  );

  return (
    <View style={[styles.root, { backgroundColor: theme.bg }]}>
      {/* Header */}
      <Animated.View
        entering={FadeInDown.duration(500)}
        style={[styles.header, { backgroundColor: theme.bgCard, borderBottomColor: theme.border }]}
      >
        <Text style={[styles.headerTitle, { color: theme.textPrimary }]}>Messages</Text>
        <View style={styles.headerRight}>
          {onlineUsers.size > 0 && (
            <Animated.View
              entering={ZoomIn.duration(400)}
              style={[styles.onlineBadge, { backgroundColor: theme.success + '20', borderColor: theme.success + '40' }]}
            >
              <View style={[styles.onlineBadgeDot, { backgroundColor: theme.success }]} />
              <Text style={[styles.onlineBadgeText, { color: theme.success }]}>
                {onlineUsers.size} online
              </Text>
            </Animated.View>
          )}
          <ThemeToggle />
        </View>
      </Animated.View>

      {loading ? (
        /* Skeleton loading */
        <View style={styles.skeletons}>
          {[0, 1, 2, 3].map((i) => (
            <View
              key={i}
              style={[styles.skeletonItem, { borderBottomColor: theme.separator }]}
            >
              <View style={[styles.skeletonAvatar, { backgroundColor: theme.skeleton }]} />
              <View style={{ flex: 1, gap: 8 }}>
                <View style={[styles.skeletonLine, { backgroundColor: theme.skeleton, width: '55%' }]} />
                <View style={[styles.skeletonLine, { backgroundColor: theme.skeleton, width: '80%', height: 10 }]} />
              </View>
            </View>
          ))}
        </View>
      ) : conversations.length === 0 ? (
        <Animated.View
          entering={FadeInDown.delay(200).duration(600)}
          style={styles.empty}
        >
          <View style={[styles.emptyIcon, { backgroundColor: theme.bgSubtle }]}>
            <Ionicons name="chatbubbles-outline" size={48} color={theme.textMuted} />
          </View>
          <Text style={[styles.emptyTitle, { color: theme.textPrimary }]}>No conversations</Text>
          <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
            Start a chat from a community{'\n'}or someone's profile.
          </Text>
        </Animated.View>
      ) : (
        <FlatList
          data={conversations}
          keyExtractor={(item) => item.id}
          renderItem={({ item, index }) => (
            <ConversationItem
              item={item}
              index={index}
              currentUser={currentUser}
              onlineUsers={onlineUsers}
              theme={theme}
              router={router}
            />
          )}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 20 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 56 : 40,
    paddingBottom: 14,
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: 24, fontWeight: '800', letterSpacing: -0.5 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  onlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
  },
  onlineBadgeDot: { width: 6, height: 6, borderRadius: 3 },
  onlineBadgeText: { fontSize: 11, fontWeight: '700' },
  convItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  avatarContainer: { position: 'relative', marginRight: 14 },
  avatar: { width: 52, height: 52, borderRadius: 26 },
  avatarPlaceholder: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: { fontWeight: '700', fontSize: 20 },
  onlineDotWrapper: {
    position: 'absolute',
    bottom: 1,
    right: 1,
    width: 14,
    height: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  onlinePulse: {
    position: 'absolute',
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#22C55E',
  },
  onlineDotCore: {
    width: 10,
    height: 14,
    borderRadius: 5,
    backgroundColor: '#22C55E',
    borderWidth: 2,
    borderColor: '#fff',
  },
  convInfo: { flex: 1 },
  convTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  convName: { fontSize: 15, fontWeight: '700', flex: 1, marginRight: 8 },
  convTime: { fontSize: 11 },
  convPreview: { fontSize: 13 },
  skeletons: { padding: 20, gap: 0 },
  skeletonItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  skeletonAvatar: { width: 52, height: 52, borderRadius: 26 },
  skeletonLine: { height: 13, borderRadius: 7 },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  emptyIcon: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: { fontSize: 20, fontWeight: '700' },
  emptySubtitle: { fontSize: 14, textAlign: 'center', lineHeight: 20 },
});

