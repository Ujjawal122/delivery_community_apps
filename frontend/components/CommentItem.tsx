import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface CommentItemProps {
  comment: any;
  onReply?: (commentId: string, full_name: string) => void;
  onUpvote?: () => void;
  onDownvote?: () => void;
  isReply?: boolean;
}

export default function CommentItem({ comment, onReply, onUpvote, onDownvote, isReply = false }: CommentItemProps) {

  return (
    <View className={`bg-white dark:bg-zinc-900 p-4 mb-2 border-b border-zinc-100 dark:border-zinc-800 ${isReply ? 'ml-8 border-l-2 border-l-blue-200 dark:border-l-blue-900 rounded-l-none' : 'rounded-xl shadow-sm'}`}>
      {/* Header */}
      <View className="flex-row items-center space-x-2 mb-2">
        <View className="w-8 h-8 bg-zinc-200 dark:bg-zinc-700 rounded-full items-center justify-center">
          <Ionicons name="person" size={16} color="gray" />
        </View>
        <View className="flex-1 ml-2">
          <View className="flex-row items-center">
            <Text className="font-semibold text-zinc-900 dark:text-zinc-100">
              {comment.author?.full_name || 'Unknown User'}
            </Text>
            {comment.replied_to_user && (
              <Text className="text-zinc-500 dark:text-zinc-400 text-xs ml-1">
                ▶ {comment.replied_to_user.full_name}
              </Text>
            )}
          </View>
          <Text className="text-xs text-zinc-500 dark:text-zinc-400">
            {new Date(comment.created_at).toLocaleString()}
          </Text>
        </View>
      </View>

      {/* Content */}
      <Text className="text-zinc-800 dark:text-zinc-200 mb-3 pl-10">
        {comment.content}
      </Text>

      {/* Action Bar */}
      <View className="flex-row items-center pl-10">
        <View className="flex-row items-center space-x-1 mr-4">
          <TouchableOpacity onPress={onUpvote} className="flex-row items-center p-1 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800">
            <Ionicons name="arrow-up-outline" size={16} color={comment.user_vote === 1 ? '#3b82f6' : 'gray'} />
            <Text className={`font-medium px-1 text-sm ${comment.user_vote === 1 ? 'text-blue-500' : 'text-zinc-600 dark:text-zinc-400'}`}>
              {comment.upvotes_count || 0}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={onDownvote} className="flex-row items-center p-1 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800">
            <Ionicons name="arrow-down-outline" size={16} color={comment.user_vote === -1 ? '#ef4444' : 'gray'} />
            <Text className={`font-medium px-1 text-sm ${comment.user_vote === -1 ? 'text-red-500' : 'text-zinc-600 dark:text-zinc-400'}`}>
              {comment.downvotes_count || 0}
            </Text>
          </TouchableOpacity>
        </View>

        {onReply && (
          <TouchableOpacity 
            className="flex-row items-center py-1 px-2 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 ml-2"
            onPress={() => onReply(isReply ? comment.parent_id : comment.id, comment.author?.full_name)}
          >
            <Ionicons name="arrow-undo-outline" size={16} color="gray" />
            <Text className="text-zinc-600 dark:text-zinc-400 font-medium ml-1 text-sm">
              Reply
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}
