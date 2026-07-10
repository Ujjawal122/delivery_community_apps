import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Modal, TextInput, Switch, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getCommunities, createCommunity } from '../api/client';
import { useColorScheme } from 'nativewind';

const PURPOSES = ['education', 'fun', 'technology', 'sports', 'gaming', 'business', 'other'];

export default function CommunitiesScreen() {
  const router = useRouter();
  const [communities, setCommunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [about, setAbout] = useState('');
  const [purpose, setPurpose] = useState('other');
  const [isPublic, setIsPublic] = useState(true);
  const [creating, setCreating] = useState(false);

  const fetchCommunities = async () => {
    try {
      const res = await getCommunities(1, 50);
      if (res.success) {
        setCommunities(res.data.items || res.data || []);
      }
    } catch (error) {
      console.warn('Failed to fetch communities', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCommunities();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchCommunities();
  };

  const handleCreate = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Community name is required');
      return;
    }

    setCreating(true);
    try {
      const res = await createCommunity({
        name,
        about: about || undefined,
        purpose,
        is_public: isPublic
      });

      if (res.success) {
        setModalVisible(false);
        // Reset form
        setName('');
        setAbout('');
        setPurpose('other');
        setIsPublic(true);
        // Refresh list
        handleRefresh();
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to create community');
    } finally {
      setCreating(false);
    }
  };

  const renderCommunity = ({ item }: { item: any }) => (
    <TouchableOpacity 
      className="bg-white dark:bg-zinc-900 p-4 mb-3 mx-4 rounded-xl shadow-sm border border-zinc-100 dark:border-zinc-800"
      onPress={() => router.push(`/community/${item.id}`)}
    >
      <View className="flex-row justify-between items-start mb-2">
        <View className="flex-1">
          <Text className="text-lg font-bold text-zinc-900 dark:text-white">c/{item.name}</Text>
          <Text className="text-xs text-zinc-500 dark:text-zinc-400">@{item.unique_name}</Text>
        </View>
        <View className="flex-row space-x-2">
          <View className="bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded-full">
            <Text className="text-xs text-blue-600 dark:text-blue-400 font-medium capitalize">{item.purpose}</Text>
          </View>
          <View className={`px-2 py-1 rounded-full ${item.is_public ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
            <Text className={`text-xs font-medium ${item.is_public ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {item.is_public ? 'Public' : 'Private'}
            </Text>
          </View>
        </View>
      </View>
      {item.about && (
        <Text className="text-sm text-zinc-700 dark:text-zinc-300 mt-2" numberOfLines={2}>
          {item.about}
        </Text>
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView className="flex-1 bg-slate-50 dark:bg-slate-900">
      <View className="px-4 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex-row justify-between items-center mt-6">
        <Text className="text-2xl font-bold text-zinc-900 dark:text-white">Communities</Text>
        <TouchableOpacity 
          className="bg-blue-600 px-3 py-2 rounded-full flex-row items-center"
          onPress={() => setModalVisible(true)}
        >
          <Ionicons name="add" size={20} color="white" />
          <Text className="text-white font-medium ml-1">Create</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color="#2563EB" />
        </View>
      ) : (
        <FlatList
          data={communities}
          keyExtractor={(item) => item.id}
          renderItem={renderCommunity}
          className="pt-4"
          refreshing={refreshing}
          onRefresh={handleRefresh}
          ListEmptyComponent={
            <View className="flex-1 justify-center items-center pt-20">
              <Ionicons name="people-outline" size={64} color="gray" />
              <Text className="text-zinc-500 dark:text-zinc-400 mt-4">No communities found</Text>
            </View>
          }
        />
      )}

      {/* Create Community Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-white dark:bg-zinc-900 rounded-t-3xl p-6 h-5/6">
            <View className="flex-row justify-between items-center mb-6">
              <Text className="text-xl font-bold text-zinc-900 dark:text-white">Create Community</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close-circle" size={28} color="gray" />
              </TouchableOpacity>
            </View>

            <Text className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Name</Text>
            <TextInput
              className="bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-white rounded-xl px-4 py-3 mb-4 border border-zinc-200 dark:border-zinc-700"
              placeholder="e.g. React Native Devs"
              placeholderTextColor="gray"
              value={name}
              onChangeText={setName}
            />

            <Text className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">About (Optional)</Text>
            <TextInput
              className="bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-white rounded-xl px-4 py-3 mb-4 border border-zinc-200 dark:border-zinc-700 h-24"
              placeholder="What is this community about?"
              placeholderTextColor="gray"
              value={about}
              onChangeText={setAbout}
              multiline
              textAlignVertical="top"
            />

            <Text className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Purpose</Text>
            <View className="flex-row flex-wrap mb-4">
              {PURPOSES.map((p) => (
                <TouchableOpacity
                  key={p}
                  onPress={() => setPurpose(p)}
                  className={`px-3 py-1.5 rounded-full mr-2 mb-2 border ${
                    purpose === p 
                      ? 'bg-blue-600 border-blue-600' 
                      : 'bg-transparent border-zinc-300 dark:border-zinc-600'
                  }`}
                >
                  <Text className={`capitalize font-medium text-sm ${
                    purpose === p ? 'text-white' : 'text-zinc-600 dark:text-zinc-300'
                  }`}>
                    {p}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View className="flex-row justify-between items-center mb-8">
              <View>
                <Text className="text-base font-medium text-zinc-900 dark:text-white">Public Community</Text>
                <Text className="text-xs text-zinc-500 dark:text-zinc-400">Anyone can view and join</Text>
              </View>
              <Switch
                value={isPublic}
                onValueChange={setIsPublic}
                trackColor={{ false: '#71717A', true: '#3B82F6' }}
              />
            </View>

            <TouchableOpacity 
              className={`py-4 rounded-xl items-center ${name ? 'bg-blue-600' : 'bg-blue-400'}`}
              onPress={handleCreate}
              disabled={creating || !name}
            >
              {creating ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold text-lg">Create Community</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}
