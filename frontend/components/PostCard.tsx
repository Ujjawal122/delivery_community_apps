import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import Animated, {
  FadeInDown,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme, POST_TYPE_META } from '../constants/theme';

interface PostCardProps {
  post: any;
  onPress?: () => void;
  onUpvote?: () => void;
  onDownvote?: () => void;
  isDetail?: boolean;
  index?: number;
}

// ── Vote Button with spring bounce ─────────────────────────────────────────
function VoteButton({
  onPress,
  icon,
  count,
  isActive,
  activeColor,
  theme,
}: {
  onPress?: () => void;
  icon: string;
  count: number;
  isActive: boolean;
  activeColor: string;
  theme: any;
}) {
  const scale = useSharedValue(1);
  const animStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  const handlePress = () => {
    scale.value = withSpring(0.7, { damping: 6 }, () => {
      scale.value = withSpring(1.15, { damping: 8 }, () => {
        scale.value = withSpring(1, { damping: 10 });
      });
    });
    onPress?.();
  };

  return (
    <Animated.View style={animStyle}>
      <TouchableOpacity
        onPress={handlePress}
        activeOpacity={0.7}
        style={[
          styles.voteBtn,
          { backgroundColor: isActive ? `${activeColor}20` : 'transparent' },
        ]}
      >
        <Ionicons
          name={icon as any}
          size={18}
          color={isActive ? activeColor : theme.textMuted}
        />
        <Text
          style={[
            styles.voteCount,
            { color: isActive ? activeColor : theme.textSecondary },
          ]}
        >
          {count}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

// ── Post Card ─────────────────────────────────────────────────────────────
export default function PostCard({
  post,
  onPress,
  onUpvote,
  onDownvote,
  isDetail = false,
  index = 0,
}: PostCardProps) {
  const router = useRouter();
  const theme = useTheme();

  const typeMeta = POST_TYPE_META[post.post_type] ?? {
    emoji: '📝',
    label: post.post_type,
    color: theme.textMuted,
    bg: theme.bgSubtle,
    darkBg: theme.bgMuted,
  };

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else if (!isDetail) {
      router.push(`/post/${post.id}`);
    }
  };

  const authorInitial = (post.author?.full_name || 'U').charAt(0).toUpperCase();

  return (
    <Animated.View entering={FadeInDown.delay(index * 60).duration(400).springify()}>
      <TouchableOpacity
        activeOpacity={isDetail ? 1 : 0.75}
        onPress={isDetail ? undefined : handlePress}
        style={[
          styles.card,
          {
            backgroundColor: theme.bgCard,
            borderColor: theme.border,
            shadowColor: theme.isDark ? '#000' : '#CBD5E1',
          },
        ]}
      >
        {/* Header row */}
        <View style={styles.headerRow}>
          {/* Author avatar */}
          {post.author?.avatar ? (
            <Image source={{ uri: post.author.avatar }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatarPlaceholder, { backgroundColor: theme.accent + '30' }]}>
              <Text style={[styles.avatarInitial, { color: theme.accent }]}>{authorInitial}</Text>
            </View>
          )}

          {/* Author info */}
          <View style={styles.authorInfo}>
            <Text style={[styles.authorName, { color: theme.textPrimary }]}>
              {post.author?.full_name || 'Unknown User'}
            </Text>
            <Text style={[styles.authorTime, { color: theme.textMuted }]}>
              {new Date(post.created_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          </View>

          {/* Post type badge */}
          <View
            style={[
              styles.typeBadge,
              {
                backgroundColor: theme.isDark ? typeMeta.darkBg : typeMeta.bg,
              },
            ]}
          >
            <Text style={styles.typeEmoji}>{typeMeta.emoji}</Text>
            <Text style={[styles.typeLabel, { color: typeMeta.color }]}>{typeMeta.label}</Text>
          </View>
        </View>

        {/* Community tag */}
        {post.community?.name && (
          <TouchableOpacity
            onPress={() => router.push(`/community/${post.community_id}`)}
            style={[styles.communityTag, { backgroundColor: theme.bgSubtle, borderColor: theme.border }]}
          >
            <Ionicons name="people" size={12} color={theme.textMuted} />
            <Text style={[styles.communityName, { color: theme.textSecondary }]}>
              {post.community.name}
            </Text>
          </TouchableOpacity>
        )}

        {/* Title */}
        <Text style={[styles.title, { color: theme.textPrimary }]}>{post.title}</Text>

        {/* Content */}
        {post.content ? (
          <Text
            style={[styles.content, { color: theme.textSecondary }]}
            numberOfLines={isDetail ? undefined : 3}
          >
            {post.content}
          </Text>
        ) : null}

        {/* Post image */}
        {post.image ? (
          <Image
            source={{ uri: post.image }}
            style={styles.postImage}
            resizeMode="cover"
          />
        ) : null}

        {/* Action bar */}
        <View style={[styles.actionBar, { borderTopColor: theme.border }]}>
          {/* Vote cluster */}
          <View style={[styles.voteCluster, { backgroundColor: theme.bgSubtle, borderColor: theme.border }]}>
            <VoteButton
              onPress={onUpvote}
              icon={post.user_vote === 1 ? 'arrow-up' : 'arrow-up-outline'}
              count={post.upvotes_count || 0}
              isActive={post.user_vote === 1}
              activeColor="#3B82F6"
              theme={theme}
            />
            <View style={[styles.voteSeparator, { backgroundColor: theme.border }]} />
            <VoteButton
              onPress={onDownvote}
              icon={post.user_vote === -1 ? 'arrow-down' : 'arrow-down-outline'}
              count={post.downvotes_count || 0}
              isActive={post.user_vote === -1}
              activeColor="#EF4444"
              theme={theme}
            />
          </View>

          {/* Comment button */}
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={isDetail ? undefined : handlePress}
          >
            <Ionicons name="chatbubble-outline" size={18} color={theme.textMuted} />
            <Text style={[styles.actionLabel, { color: theme.textSecondary }]}>Comments</Text>
          </TouchableOpacity>

          <View style={{ flex: 1 }} />

          {/* Share */}
          <TouchableOpacity style={styles.actionBtn}>
            <Ionicons name="share-social-outline" size={18} color={theme.textMuted} />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 10,
  },
  avatar: { width: 40, height: 40, borderRadius: 20 },
  avatarPlaceholder: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: { fontWeight: '700', fontSize: 16 },
  authorInfo: { flex: 1 },
  authorName: { fontWeight: '600', fontSize: 14 },
  authorTime: { fontSize: 11, marginTop: 1 },
  typeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  typeEmoji: { fontSize: 12 },
  typeLabel: { fontSize: 11, fontWeight: '700' },
  communityTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 8,
  },
  communityName: { fontSize: 11, fontWeight: '600' },
  title: { fontSize: 16, fontWeight: '700', lineHeight: 22, marginBottom: 6 },
  content: { fontSize: 14, lineHeight: 20, marginBottom: 10 },
  postImage: { width: '100%', height: 180, borderRadius: 12, marginBottom: 10 },
  actionBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 10,
    borderTopWidth: 1,
    gap: 8,
  },
  voteCluster: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 20,
    borderWidth: 1,
    overflow: 'hidden',
  },
  voteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  voteCount: { fontSize: 13, fontWeight: '600' },
  voteSeparator: { width: 1, height: 18 },
  actionBtn: { flexDirection: 'row', alignItems: 'center', gap: 5, padding: 6 },
  actionLabel: { fontSize: 13, fontWeight: '500' },
});
