import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, TextInput, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { useLocalSearchParams, Stack, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getPost, getComments, addComment, votePost, voteComment } from '../api/client';
import PostCard from '../../components/PostCard';
import CommentItem from '../../components/CommentItem';

export default function PostScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  
  const [post, setPost] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [replyingTo, setReplyingTo] = useState<{ id: string, full_name: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchPostDetails = useCallback(async () => {
    if (!id) return;
    try {
      const [postRes, commentsRes] = await Promise.all([
        getPost(id as string),
        getComments(id as string, 1, 100)
      ]);
      
      if (postRes.success) setPost(postRes.data);
      if (commentsRes.success) {
        // Flatten nested comments for display or we can just render the top level and recursive in CommentItem if we want.
        // The backend returns nested replies. For now, we will render a flat list if possible, or handle nested.
        // Let's assume the API returns a flat list or we flatten it.
        // To simplify, let's just set them.
        let flatComments: any[] = [];
        const flatten = (items: any[], level = 0) => {
          items.forEach(c => {
            flatComments.push({ ...c, _level: level });
            if (c.replies && c.replies.length > 0) {
              flatten(c.replies, level + 1);
            }
          });
        };
        const commentsData = Array.isArray(commentsRes.data) ? commentsRes.data : (commentsRes.data?.items || []);
        flatten(commentsData);
        setComments(flatComments);
      }
    } catch (error) {
      console.error('Failed to fetch post details:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchPostDetails();
  }, [fetchPostDetails]);

  const handlePostVote = async (voteType: number) => {
    if (!post) return;
    
    const currentVote = post.user_vote;
    const newVote = currentVote === voteType ? null : voteType;
    
    // Optimistic update
    let up = post.upvotes_count;
    let down = post.downvotes_count;
    
    if (currentVote === 1) up = Math.max(0, up - 1);
    if (currentVote === -1) down = Math.max(0, down - 1);
    
    if (newVote === 1) up++;
    if (newVote === -1) down++;

    setPost({
      ...post,
      upvotes_count: up,
      downvotes_count: down,
      user_vote: newVote
    });

    try {
      await votePost(post.id, voteType);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCommentVote = async (commentId: string, voteType: number) => {
    try {
      await voteComment(post.id, commentId, voteType);
      // Optimistic update
      setComments(prev => prev.map(c => {
        if (c.id === commentId) {
          return {
            ...c,
            upvotes_count: (c.upvotes_count || 0) + (voteType === 1 ? 1 : 0),
            downvotes_count: (c.downvotes_count || 0) + (voteType === -1 ? 1 : 0)
          };
        }
        return c;
      }));
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmitComment = async () => {
    if (!commentText.trim() || !post) return;
    setSubmitting(true);
    try {
      await addComment(post.id, commentText, replyingTo?.id);
      setCommentText('');
      setReplyingTo(null);
      fetchPostDetails(); // Refresh to get the new comment
    } catch (error) {
      console.error('Failed to add comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <View className="flex-1 justify-center items-center bg-zinc-50 dark:bg-black">
        <ActivityIndicator size="large" color="gray" />
      </View>
    );
  }

  if (!post) {
    return (
      <View className="flex-1 justify-center items-center bg-zinc-50 dark:bg-black">
        <Text className="text-zinc-500">Post not found.</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      className="flex-1 bg-zinc-50 dark:bg-black" 
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <Stack.Screen options={{ title: 'Post Details', headerBackTitle: 'Back' }} />
      
      <FlatList
        data={comments}
        keyExtractor={item => item.id}
        ListHeaderComponent={
          <View className="p-4 pb-0">
            <PostCard 
              post={post} 
              isDetail={true} 
              onUpvote={() => handlePostVote(1)}
              onDownvote={() => handlePostVote(-1)}
            />
            <Text className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-2 px-1">
              Comments
            </Text>
          </View>
        }
        contentContainerStyle={{ paddingBottom: 20 }}
        renderItem={({ item }) => (
          <View className="px-4">
            <CommentItem 
              comment={item} 
              isReply={item._level > 0}
              onReply={(cid, user) => setReplyingTo({ id: cid, full_name: user })}
              onUpvote={() => handleCommentVote(item.id, 1)}
              onDownvote={() => handleCommentVote(item.id, -1)}
            />
          </View>
        )}
        ListEmptyComponent={
          <View className="py-8 items-center">
            <Text className="text-zinc-500">No comments yet. Be the first!</Text>
          </View>
        }
      />

      {/* Comment Input */}
      <View className="p-3 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800">
        {replyingTo && (
          <View className="flex-row items-center justify-between bg-zinc-100 dark:bg-zinc-800 p-2 mb-2 rounded-lg">
            <Text className="text-zinc-600 dark:text-zinc-400 text-sm">
              Replying to <Text className="font-semibold">{replyingTo.full_name}</Text>
            </Text>
            <TouchableOpacity onPress={() => setReplyingTo(null)}>
              <Ionicons name="close-circle" size={20} color="gray" />
            </TouchableOpacity>
          </View>
        )}
        <View className="flex-row items-center">
          <TextInput
            className="flex-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-full px-4 py-2 mr-2 max-h-32"
            placeholder="Add a comment..."
            placeholderTextColor="gray"
            multiline
            value={commentText}
            onChangeText={setCommentText}
          />
          <TouchableOpacity 
            className={`w-10 h-10 rounded-full items-center justify-center ${commentText.trim() ? 'bg-blue-600' : 'bg-zinc-300 dark:bg-zinc-700'}`}
            onPress={handleSubmitComment}
            disabled={!commentText.trim() || submitting}
          >
            {submitting ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Ionicons name="send" size={16} color={commentText.trim() ? "white" : "gray"} />
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
