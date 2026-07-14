import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Alert, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { getCommunity, checkCommunityMembership, joinCommunity, getCommunityPosts, votePost } from '../api/client';
import PostCard from '../../components/PostCard';
import { useColorScheme } from 'nativewind';
import { Ionicons } from '@expo/vector-icons';

export default function CommunityScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const { colorScheme } = useColorScheme();

  const [community, setCommunity] = useState<any>(null);
  const [membership, setMembership] = useState<any>(null);
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [postsLoading, setPostsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const isDark = colorScheme === 'dark';

  const fetchData = async () => {
    try {
      setLoading(true);
      const [commRes, memRes] = await Promise.all([
        getCommunity(id as string),
        checkCommunityMembership(id as string)
      ]);
      setCommunity(commRes.data);
      setMembership(memRes.data);

      // If user is member, fetch posts
      if (memRes.data?.is_member) {
        fetchPosts();
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Failed to load community details');
    } finally {
      setLoading(false);
    }
  };

  const fetchPosts = async () => {
    try {
      setPostsLoading(true);
      const res = await getCommunityPosts(id as string);
      setPosts(res.data.items || []);
    } catch (error) {
      console.error(error);
    } finally {
      setPostsLoading(false);
      setRefreshing(false);
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

  useEffect(() => {
    if (id) fetchData();
  }, [id]);

  const handleJoin = async () => {
    try {
      setLoading(true);
      const res = await joinCommunity(id as string);
      Alert.alert('Success', res.data?.status === 'pending' ? 'Join request sent!' : 'You have joined the community!');
      fetchData(); // Refresh state
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Could not process join request');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading && !community) {
    return (
      <View className="flex-1 justify-center items-center dark:bg-slate-900 bg-white">
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  if (!community) {
    return (
      <View className="flex-1 justify-center items-center dark:bg-slate-900 bg-white">
        <Text className="text-slate-800 dark:text-slate-200">Community not found.</Text>
      </View>
    );
  }

  const isMember = membership?.is_member;
  const isPending = membership?.join_request_status === 'pending';

  return (
    <SafeAreaView className="flex-1 dark:bg-slate-900 bg-slate-50" edges={['top']}>
      <View className="flex-row items-center px-4 py-3 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <TouchableOpacity onPress={() => router.back()} className="mr-3">
          <Ionicons name="arrow-back" size={24} color={isDark ? 'white' : 'black'} />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-bold text-slate-900 dark:text-white" numberOfLines={1}>{community.name}</Text>
          <Text className="text-sm text-slate-500 dark:text-slate-400 capitalize">{community.purpose} • {community.is_public ? 'Public' : 'Private'}</Text>
        </View>
        {!isMember && (
          <TouchableOpacity
            className={`px-4 py-2 rounded-full ${isPending ? 'bg-slate-200 dark:bg-slate-700' : 'bg-blue-500'}`}
            onPress={handleJoin}
            disabled={isPending || loading}
          >
            <Text className={`font-semibold ${isPending ? 'text-slate-600 dark:text-slate-300' : 'text-white'}`}>
              {isPending ? 'Pending' : 'Join'}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {community.about && (
        <View className="px-4 py-3 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
          <Text className="text-slate-700 dark:text-slate-300">{community.about}</Text>
        </View>
      )}

      {/* Creator Info */}
      {community.creator && (
        <View className="px-4 py-3 bg-white dark:bg-slate-800 mb-2 border-b border-slate-200 dark:border-slate-700 flex-row items-center">
          <Text className="text-slate-500 dark:text-slate-400 text-sm mr-2">Created by</Text>
          {community.creator.avatar ? (
            <Image source={{ uri: community.creator.avatar }} className="w-6 h-6 rounded-full mr-2" />
          ) : (
            <View className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 items-center justify-center mr-2">
              <Text className="text-blue-600 dark:text-blue-300 text-xs font-bold">
                {community.creator.full_name.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          <Text className="text-slate-800 dark:text-slate-200 font-medium">
            {community.creator.full_name}
          </Text>
        </View>
      )}

      {isMember ? (
        <FlatList
          data={posts}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <PostCard
              post={item}
              onPress={() => router.push(`/post/${item.id}`)}
              onUpvote={() => handleVote(item.id, item.user_vote, 1)}
              onDownvote={() => handleVote(item.id, item.user_vote, -1)}
            />
          )}
          contentContainerStyle={{ padding: 12, paddingBottom: 80 }}
          refreshing={refreshing}
          onRefresh={handleRefresh}
          ListEmptyComponent={
            postsLoading ? <ActivityIndicator size="small" color="#3b82f6" style={{ marginTop: 20 }} /> : <Text className="text-center text-slate-500 mt-4">No posts yet in this community.</Text>
          }
        />
      ) : (
        <View className="flex-1 justify-center items-center px-6">
          <Ionicons name="lock-closed" size={48} color={isDark ? '#475569' : '#94a3b8'} />
          <Text className="text-center text-slate-500 dark:text-slate-400 mt-4 text-lg">
            {community.is_public ? "Join this community to see its posts!" : "This is a private community. Request to join to see its posts!"}
          </Text>
        </View>
      )}

      {isMember && (
        <TouchableOpacity
          className="absolute bottom-6 right-6 w-14 h-14 bg-blue-600 rounded-full items-center justify-center shadow-lg"
          onPress={() => router.push(`/create?community_id=${community.id}&community_name=${encodeURIComponent(community.name)}`)}
        >
          <Ionicons name="add" size={28} color="white" />
        </TouchableOpacity>
      )}
    </SafeAreaView>
  );
}
