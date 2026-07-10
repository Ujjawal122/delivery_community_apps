import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, RefreshControl, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getFeed, votePost, removeVotePost } from '../api/client';
import PostCard from '../../components/PostCard';
import { useAuthStore } from '../../store/authStore';

export default function Home() {
  const router = useRouter();
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const { isAuthenticated } = useAuthStore();

  const fetchPosts = async (pageNumber = 1, shouldRefresh = false) => {
    try {
      // We pass 0, 0 for lat, long for now, radius_km 50
      const response = await getFeed(pageNumber, 10, 0, 0, 50);
      if (response.success) {
        const newPosts = response.data.items;
        if (shouldRefresh) {
          setPosts(newPosts);
        } else {
          setPosts(prev => [...prev, ...newPosts]);
        }
        setHasMore(newPosts.length === 10);
      }
    } catch (error) {
      // Just log instead of error so it doesn't pop up a RedBox for typical API errors (like 401s before redirect)
      console.log('Failed to fetch feed:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchPosts();
    }
  }, [isAuthenticated]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setPage(1);
    fetchPosts(1, true);
  }, []);

  const loadMore = () => {
    if (!loading && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchPosts(nextPage);
    }
  };

  const handleVote = async (postId: string, currentVote: number | null | undefined, voteType: number) => {
    const newVote = currentVote === voteType ? null : voteType;

    // Optimistic UI update
    setPosts(prev => prev.map(post => {
      if (post.id === postId) {
        let up = post.upvotes_count;
        let down = post.downvotes_count;
        
        // Remove old vote
        if (currentVote === 1) up = Math.max(0, up - 1);
        if (currentVote === -1) down = Math.max(0, down - 1);
        
        // Add new vote
        if (newVote === 1) up++;
        if (newVote === -1) down++;
        
        return { ...post, upvotes_count: up, downvotes_count: down, user_vote: newVote };
      }
      return post;
    }));

    try {
      await votePost(postId, voteType);
    } catch (error) {
      console.error('Vote failed:', error);
    }
  };

  const renderFooter = () => {
    if (!loading) return null;
    return (
      <View className="py-4">
        <ActivityIndicator size="small" color="gray" />
      </View>
    );
  };

  return (
    <View className="flex-1 bg-zinc-50 dark:bg-black">
      <FlatList
        data={posts}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <PostCard 
            post={item} 
            onUpvote={() => handleVote(item.id, item.user_vote, 1)}
            onDownvote={() => handleVote(item.id, item.user_vote, -1)}
          />
        )}
        contentContainerStyle={{ padding: 16 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={
          !loading ? (
            <View className="flex-1 items-center justify-center pt-20">
              <Text className="text-zinc-500 dark:text-zinc-400">No posts in your area yet.</Text>
            </View>
          ) : null
        }
      />

      {/* Floating Action Button (FAB) for Creating Posts */}
      <TouchableOpacity
        className="absolute bottom-6 right-6 w-14 h-14 bg-blue-600 rounded-full items-center justify-center shadow-lg"
        onPress={() => router.push('/create')}
        activeOpacity={0.8}
      >
        <Ionicons name="add" size={32} color="white" />
      </TouchableOpacity>
    </View>
  );
}
