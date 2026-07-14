import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import Animated, {
  FadeInDown,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  withSpring,
} from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { Ionicons, Feather } from '@expo/vector-icons';
import { getFeed, votePost } from '../api/client';
import PostCard from '../../components/PostCard';
import { useAuthStore } from '../../store/authStore';
import { useTheme } from '../../constants/theme';
import Header from '../../components/Header';

// ── Skeleton Card ─────────────────────────────────────────────────────────
function SkeletonCard({ theme }: { theme: any }) {
  const opacity = useSharedValue(1);

  useEffect(() => {
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.4, { duration: 800 }),
        withTiming(1, { duration: 800 })
      ),
      -1,
      true
    );
  }, []);

  const animStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <Animated.View
      style={[
        styles.skeletonCard,
        { backgroundColor: theme.bgCard, borderColor: theme.border },
        animStyle,
      ]}
    >
      <View style={styles.skeletonHeader}>
        <View style={[styles.skeletonAvatar, { backgroundColor: theme.skeleton }]} />
        <View style={{ flex: 1, gap: 6 }}>
          <View style={[styles.skeletonLine, { backgroundColor: theme.skeleton, width: '50%' }]} />
          <View style={[styles.skeletonLine, { backgroundColor: theme.skeleton, width: '30%', height: 8 }]} />
        </View>
      </View>
      <View style={[styles.skeletonLine, { backgroundColor: theme.skeleton, width: '90%', marginBottom: 8 }]} />
      <View style={[styles.skeletonLine, { backgroundColor: theme.skeleton, width: '70%', height: 12 }]} />
    </Animated.View>
  );
}

export default function Home() {
  const router = useRouter();
  const theme = useTheme();
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [fetchingMore, setFetchingMore] = useState(false);
  const { isAuthenticated } = useAuthStore();

  // FAB rotation animation
  const fabRotate = useSharedValue(0);
  const fabStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${fabRotate.value}deg` }],
  }));

  const fetchPosts = async (pageNumber = 1, shouldRefresh = false) => {
    if (pageNumber > 1) setFetchingMore(true);
    try {
      const response = await getFeed(pageNumber, 10, 0, 0, 50);
      if (response.success) {
        const newPosts = response.data.items;
        if (shouldRefresh) {
          setPosts(newPosts);
        } else {
          setPosts((prev) => {
            const existingIds = new Set(prev.map(p => p.id));
            const uniqueNewPosts = newPosts.filter((p: any) => !existingIds.has(p.id));
            return [...prev, ...uniqueNewPosts];
          });
        }
        setHasMore(newPosts.length === 10);
      }
    } catch (error) {
      console.log('Failed to fetch feed:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
      setFetchingMore(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) fetchPosts();
  }, [isAuthenticated]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setPage(1);
    fetchPosts(1, true);
  }, []);

  const loadMore = () => {
    if (!loading && !fetchingMore && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchPosts(nextPage);
    }
  };

  const handleVote = async (postId: string, currentVote: number | null | undefined, voteType: number) => {
    const newVote = currentVote === voteType ? null : voteType;
    setPosts((prev) =>
      prev.map((post) => {
        if (post.id === postId) {
          let up = post.upvotes_count;
          let down = post.downvotes_count;
          if (currentVote === 1) up = Math.max(0, up - 1);
          if (currentVote === -1) down = Math.max(0, down - 1);
          if (newVote === 1) up++;
          if (newVote === -1) down++;
          return { ...post, upvotes_count: up, downvotes_count: down, user_vote: newVote };
        }
        return post;
      })
    );
    try {
      await votePost(postId, voteType);
    } catch (error) {
      console.error('Vote failed:', error);
    }
  };

  const renderFooter = () => {
    if (!hasMore) return null;
    return (
      <View style={styles.footer}>
        <ActivityIndicator size="small" color={theme.accent} />
      </View>
    );
  };

  const renderEmpty = () => {
    if (loading) return null;
    return (
      <Animated.View entering={FadeInDown.duration(600)} style={styles.empty}>
        <Ionicons name="newspaper-outline" size={64} color={theme.textMuted} />
        <Text style={[styles.emptyTitle, { color: theme.textPrimary }]}>No posts yet</Text>
        <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
          Be the first to share something!
        </Text>
      </Animated.View>
    );
  };

  return (
    <View style={[styles.root, { backgroundColor: theme.bg }]}>
      <Header title="Feed" />

      {/* Content */}
      {loading && posts.length === 0 ? (
        <View style={styles.skeletons}>
          {[0, 1, 2].map((i) => (
            <SkeletonCard key={i} theme={theme} />
          ))}
        </View>
      ) : (
        <FlatList
          data={posts}
          keyExtractor={(item) => item.id}
          renderItem={({ item, index }) => (
            <PostCard
              post={item}
              index={index}
              onUpvote={() => handleVote(item.id, item.user_vote, 1)}
              onDownvote={() => handleVote(item.id, item.user_vote, -1)}
            />
          )}
          contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.accent}
              colors={[theme.accent]}
            />
          }
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={renderFooter}
          ListEmptyComponent={renderEmpty}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Animated FAB */}
      <Animated.View style={[styles.fab, { backgroundColor: theme.accent }, fabStyle]}>
        <TouchableOpacity
          onPress={() => {
            fabRotate.value = withSequence(
              withSpring(45, { damping: 8 }),
              withTiming(45, { duration: 100 })
            );
            setTimeout(() => {
              fabRotate.value = withSpring(0, { damping: 10 });
              router.push('/create');
            }, 150);
          }}
          style={styles.fabInner}
          activeOpacity={0.85}
        >
          <Ionicons name="add" size={30} color="#ffffff" />
        </TouchableOpacity>
      </Animated.View>
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
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoSmall: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5 },
  skeletons: { padding: 16, gap: 12 },
  skeletonCard: {
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    gap: 12,
  },
  skeletonHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  skeletonAvatar: { width: 40, height: 40, borderRadius: 20 },
  skeletonLine: { height: 14, borderRadius: 7, marginBottom: 0 },
  footer: { paddingVertical: 20, alignItems: 'center' },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80, gap: 12 },
  emptyTitle: { fontSize: 20, fontWeight: '700' },
  emptySubtitle: { fontSize: 14, textAlign: 'center' },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 20,
    width: 58,
    height: 58,
    borderRadius: 29,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 8,
  },
  fabInner: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
