import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

interface PostCardProps {
  post: any;
  onPress?: () => void;
  onUpvote?: () => void;
  onDownvote?: () => void;
  isDetail?: boolean;
}

export default function PostCard({ post, onPress, onUpvote, onDownvote, isDetail = false }: PostCardProps) {
  const router = useRouter();

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else if (!isDetail) {
      router.push(`/post/${post.id}`);
    }
  };

  return (
    <TouchableOpacity 
      activeOpacity={isDetail ? 1 : 0.7} 
      onPress={isDetail ? undefined : handlePress}
      className="bg-white dark:bg-zinc-900 rounded-2xl p-4 mb-4 shadow-sm border border-zinc-100 dark:border-zinc-800"
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center space-x-2">
          <View className="w-10 h-10 bg-zinc-200 dark:bg-zinc-700 rounded-full items-center justify-center">
            <Ionicons name="person" size={20} color="gray" />
          </View>
          <View className="ml-2">
            <Text className="font-semibold text-zinc-900 dark:text-zinc-100">
              {post.author?.full_name || 'Unknown User'}
            </Text>
            <Text className="text-xs text-zinc-500 dark:text-zinc-400">
              {new Date(post.created_at).toLocaleString()}
            </Text>
          </View>
        </View>
        <View className="flex-row items-center space-x-2">
          {post.community_id && (
            <TouchableOpacity 
              onPress={() => router.push(`/community/${post.community_id}`)}
              className="bg-purple-100 dark:bg-purple-900/30 px-3 py-1 rounded-full"
            >
              <Text className="text-xs font-medium text-purple-600 dark:text-purple-400">
                Community
              </Text>
            </TouchableOpacity>
          )}
          <View className="bg-blue-100 dark:bg-blue-900/30 px-3 py-1 rounded-full">
            <Text className="text-xs font-medium text-blue-600 dark:text-blue-400">
              {post.post_type}
            </Text>
          </View>
        </View>
      </View>

      {/* Content */}
      <Text className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-2">
        {post.title}
      </Text>
      {post.content && (
        <Text className="text-zinc-700 dark:text-zinc-300 mb-4 leading-5" numberOfLines={isDetail ? undefined : 3}>
          {post.content}
        </Text>
      )}

    {/* Action Bar */}
    <View className="flex-row items-center pt-3 border-t border-zinc-100 dark:border-zinc-800">
      <View className="flex-row items-center bg-zinc-100 dark:bg-zinc-800 rounded-full px-1 py-1 mr-4">
        <TouchableOpacity onPress={onUpvote} className="p-2 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700">
          <Ionicons name="arrow-up-outline" size={20} color={post.user_vote === 1 ? '#3b82f6' : 'gray'} />
        </TouchableOpacity>
        <Text className="font-semibold text-zinc-700 dark:text-zinc-300 px-2">
          {post.upvotes_count - post.downvotes_count}
        </Text>
        <TouchableOpacity onPress={onDownvote} className="p-2 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700">
          <Ionicons name="arrow-down-outline" size={20} color={post.user_vote === -1 ? '#ef4444' : 'gray'} />
        </TouchableOpacity>
      </View>

        <TouchableOpacity className="flex-row items-center p-2" onPress={isDetail ? undefined : handlePress}>
          <Ionicons name="chatbubble-outline" size={20} color="gray" />
          <Text className="text-zinc-600 dark:text-zinc-400 font-medium ml-2">
            Comments
          </Text>
        </TouchableOpacity>

        <View className="flex-1" />
        
        <TouchableOpacity className="p-2">
          <Ionicons name="share-social-outline" size={20} color="gray" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
}
