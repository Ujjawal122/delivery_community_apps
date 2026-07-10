import { View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import apiClient from './api/client';

const POST_TYPES = ['question', 'share', 'discussion', 'tip', 'news'];

export default function CreatePostScreen() {
  const router = useRouter();
  const { community_id, community_name } = useLocalSearchParams();
  
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [postType, setPostType] = useState('discussion');
  const [loading, setLoading] = useState(false);

  const handlePost = async () => {
    if (!title) {
      Alert.alert('Error', 'Title is required');
      return;
    }

    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Location permission is required to create a post.');
        setLoading(false);
        return;
      }

      let latitude = null;
      let longitude = null;
      try {
        const location = await Location.getCurrentPositionAsync({});
        latitude = location.coords.latitude;
        longitude = location.coords.longitude;
      } catch (err) {
        Alert.alert('Error', 'Could not fetch your current location. Please try again.');
        setLoading(false);
        return;
      }

      const res = await apiClient.post('/posts', {
        title,
        content: content || null,
        post_type: postType,
        community_id: community_id || null,
        latitude,
        longitude
      });

      if (res.data.success) {
        // Go back and we could theoretically trigger a refresh on the feed
        router.back();
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to create post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="flex-1 bg-slate-50 dark:bg-slate-900 pt-6 px-4">
      <View className="flex-row justify-between items-center mb-6">
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="close" size={28} className="text-slate-900 dark:text-white" />
        </TouchableOpacity>
        <Text className="text-xl font-bold text-zinc-900 dark:text-white">Create Post</Text>
        <TouchableOpacity onPress={handlePost} disabled={loading || !title}>
          {loading ? (
            <ActivityIndicator color="#2563EB" />
          ) : (
            <Text className={`font-bold text-lg ${title ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}`}>Post</Text>
          )}
        </TouchableOpacity>
      </View>

      {community_name && (
        <View className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-xl mb-4 border border-blue-100 dark:border-blue-800">
          <Text className="text-blue-700 dark:text-blue-300 font-medium text-center">
            Posting in c/{community_name}
          </Text>
        </View>
      )}

      <TextInput
        className="text-2xl font-bold text-slate-900 dark:text-white mb-4"
        placeholder="An interesting title"
        placeholderTextColor="gray"
        value={title}
        onChangeText={setTitle}
        autoFocus
      />

      <TextInput
        className="text-base text-slate-700 dark:text-slate-300 mb-6"
        placeholder="What do you want to share? (Optional)"
        placeholderTextColor="gray"
        value={content}
        onChangeText={setContent}
        multiline
        textAlignVertical="top"
        style={{ minHeight: 120 }}
      />

      <Text className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Category</Text>
      <View className="flex-row flex-wrap">
        {POST_TYPES.map((type) => (
          <TouchableOpacity
            key={type}
            onPress={() => setPostType(type)}
            className={`px-4 py-2 rounded-full mr-2 mb-2 border ${
              postType === type 
                ? 'bg-blue-600 border-blue-600' 
                : 'bg-transparent border-slate-300 dark:border-slate-600'
            }`}
          >
            <Text className={`capitalize font-semibold ${
              postType === type ? 'text-white' : 'text-slate-600 dark:text-slate-300'
            }`}>
              {type}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}
