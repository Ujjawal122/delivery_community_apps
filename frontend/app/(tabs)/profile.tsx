import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Image, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { getProfile, updateProfile } from '../api/client';
import { useAuthStore } from '../../store/authStore';

export default function ProfileScreen() {
  const router = useRouter();
  const { logout, user: authUser, setUser } = useAuthStore();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState<any>(null);

  // Form state
  const [formData, setFormData] = useState({
    full_name: '',
    bio: '',
    company: '',
    vehicle_type: '',
    phone_number: '',
  });

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await getProfile();
      if (response.success) {
        setProfile(response.data);
        setFormData({
          full_name: response.data.full_name || '',
          bio: response.data.bio || '',
          company: response.data.company || '',
          vehicle_type: response.data.vehicle_type || '',
          phone_number: response.data.phone_number || '',
        });
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      Alert.alert('Error', 'Failed to load profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await updateProfile(formData);
      if (response.success) {
        setProfile(response.data);
        // Also update auth store if it caches user data
        if (authUser) {
          setUser({ ...authUser, ...response.data });
        }
        setIsEditing(false);
        Alert.alert('Success', 'Profile updated successfully.');
      }
    } catch (error) {
      console.error('Failed to update profile:', error);
      Alert.alert('Error', 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  if (loading) {
    return (
      <View className="flex-1 justify-center items-center bg-zinc-50 dark:bg-black">
        <ActivityIndicator size="large" color="gray" />
      </View>
    );
  }

  if (!profile) {
    return (
      <View className="flex-1 justify-center items-center bg-zinc-50 dark:bg-black">
        <Text className="text-zinc-500">Could not load profile.</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      className="flex-1 bg-zinc-50 dark:bg-black"
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        {/* Header / Avatar */}
        <View className="items-center mb-8">
          {profile.avatar ? (
            <Image 
              source={{ uri: profile.avatar }} 
              className="w-24 h-24 rounded-full mb-3 bg-zinc-200" 
            />
          ) : (
            <View className="w-24 h-24 rounded-full bg-zinc-200 dark:bg-zinc-800 items-center justify-center mb-3">
              <Ionicons name="person" size={50} color="gray" />
            </View>
          )}
          
          {!isEditing && (
            <>
              <Text className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">{profile.full_name}</Text>
              <Text className="text-zinc-500 dark:text-zinc-400">{profile.email}</Text>
              {profile.is_verified && (
                <View className="flex-row items-center mt-2 bg-green-100 dark:bg-green-900/30 px-3 py-1 rounded-full">
                  <Ionicons name="checkmark-circle" size={16} color="green" />
                  <Text className="text-green-700 dark:text-green-400 font-medium ml-1 text-xs">Verified</Text>
                </View>
              )}
            </>
          )}
        </View>

        {isEditing ? (
          /* Edit Mode */
          <View className="space-y-4">
            <View>
              <Text className="text-zinc-600 dark:text-zinc-400 mb-1 ml-1 text-sm">Full Name</Text>
              <TextInput
                className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 text-zinc-900 dark:text-zinc-100"
                value={formData.full_name}
                onChangeText={(text) => setFormData(prev => ({ ...prev, full_name: text }))}
                placeholder="Full Name"
                placeholderTextColor="gray"
              />
            </View>

            <View>
              <Text className="text-zinc-600 dark:text-zinc-400 mb-1 ml-1 text-sm">Bio</Text>
              <TextInput
                className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 text-zinc-900 dark:text-zinc-100 min-h-[80px]"
                value={formData.bio}
                onChangeText={(text) => setFormData(prev => ({ ...prev, bio: text }))}
                placeholder="Tell us about yourself..."
                placeholderTextColor="gray"
                multiline
              />
            </View>

            <View>
              <Text className="text-zinc-600 dark:text-zinc-400 mb-1 ml-1 text-sm">Company</Text>
              <TextInput
                className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 text-zinc-900 dark:text-zinc-100"
                value={formData.company}
                onChangeText={(text) => setFormData(prev => ({ ...prev, company: text }))}
                placeholder="Company Name"
                placeholderTextColor="gray"
              />
            </View>

            <View>
              <Text className="text-zinc-600 dark:text-zinc-400 mb-1 ml-1 text-sm">Vehicle Type</Text>
              <TextInput
                className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 text-zinc-900 dark:text-zinc-100"
                value={formData.vehicle_type}
                onChangeText={(text) => setFormData(prev => ({ ...prev, vehicle_type: text }))}
                placeholder="e.g. Bicycle, Van, Scooter"
                placeholderTextColor="gray"
              />
            </View>

            <View>
              <Text className="text-zinc-600 dark:text-zinc-400 mb-1 ml-1 text-sm">Phone Number</Text>
              <TextInput
                className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 text-zinc-900 dark:text-zinc-100"
                value={formData.phone_number}
                onChangeText={(text) => setFormData(prev => ({ ...prev, phone_number: text }))}
                placeholder="Phone Number"
                placeholderTextColor="gray"
                keyboardType="phone-pad"
              />
            </View>

            <View className="flex-row space-x-3 mt-4">
              <TouchableOpacity 
                className="flex-1 bg-zinc-200 dark:bg-zinc-800 p-4 rounded-xl items-center"
                onPress={() => setIsEditing(false)}
                disabled={saving}
              >
                <Text className="text-zinc-700 dark:text-zinc-300 font-bold">Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                className="flex-1 bg-blue-600 p-4 rounded-xl items-center"
                onPress={handleSave}
                disabled={saving}
              >
                {saving ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text className="text-white font-bold">Save Changes</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          /* View Mode */
          <View className="bg-white dark:bg-zinc-900 rounded-2xl p-5 shadow-sm border border-zinc-100 dark:border-zinc-800">
            <View className="mb-4">
              <Text className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-1">About</Text>
              <Text className="text-zinc-800 dark:text-zinc-200 text-base">{profile.bio || 'No bio provided.'}</Text>
            </View>

            <View className="h-[1px] bg-zinc-100 dark:bg-zinc-800 my-2" />

            <View className="py-2 flex-row items-center">
              <Ionicons name="briefcase-outline" size={20} color="gray" />
              <Text className="text-zinc-700 dark:text-zinc-300 ml-3 text-base">{profile.company || 'Not specified'}</Text>
            </View>

            <View className="py-2 flex-row items-center">
              <Ionicons name="bicycle-outline" size={20} color="gray" />
              <Text className="text-zinc-700 dark:text-zinc-300 ml-3 text-base">{profile.vehicle_type || 'Not specified'}</Text>
            </View>

            <View className="py-2 flex-row items-center">
              <Ionicons name="call-outline" size={20} color="gray" />
              <Text className="text-zinc-700 dark:text-zinc-300 ml-3 text-base">{profile.phone_number || 'Not specified'}</Text>
            </View>

            <View className="h-[1px] bg-zinc-100 dark:bg-zinc-800 my-4" />

            <TouchableOpacity 
              className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-xl items-center mb-3"
              onPress={() => setIsEditing(true)}
            >
              <Text className="text-blue-700 dark:text-blue-400 font-bold">Edit Profile</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              className="bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 p-4 rounded-xl items-center"
              onPress={handleLogout}
            >
              <Text className="text-red-600 dark:text-red-400 font-bold">Logout</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
