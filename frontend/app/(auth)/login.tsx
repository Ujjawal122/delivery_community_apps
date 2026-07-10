import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import apiClient from '../api/client';
import { useColorScheme } from 'nativewind';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const router = useRouter();
  const { login } = useAuthStore();
  const { colorScheme } = useColorScheme();

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password,
      });

      if (response.data.success) {
        const { access_token, refresh_token, user } = response.data.data;
        await login(access_token, refresh_token, user);
        // Authentication state is watched by the root layout, 
        // which will automatically redirect to the (tabs) group.
      } else {
        setError(response.data.message || 'Login failed');
      }
    } catch (err: any) {
      setError(
        err.response?.data?.message || 'An error occurred during login. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-white dark:bg-black"
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 24 }}
        keyboardShouldPersistTaps="handled"
      >
        <View className="mb-10 items-center">
          <View className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-full mb-4">
            <Feather name="truck" size={48} color="#3b82f6" />
          </View>
          <Text className="text-3xl font-bold text-gray-900 dark:text-white mb-2 text-center">
            Welcome Back
          </Text>
          <Text className="text-base text-gray-500 dark:text-gray-400 text-center">
            Sign in to continue to Delivery Community
          </Text>
        </View>

        {error ? (
          <View className="bg-red-100 border-l-4 border-red-500 p-4 mb-6 rounded-r-md">
            <Text className="text-red-700">{error}</Text>
          </View>
        ) : null}

        <View className="mb-6">
          <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email Address
          </Text>
          <View className="flex-row items-center border border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900 px-4 py-3">
            <Feather name="mail" size={20} color={colorScheme === 'dark' ? '#9ca3af' : '#6b7280'} />
            <TextInput
              className="flex-1 ml-3 text-base text-gray-900 dark:text-white"
              placeholder="Enter your email"
              placeholderTextColor={colorScheme === 'dark' ? '#6b7280' : '#9ca3af'}
              keyboardType="email-address"
              autoCapitalize="none"
              value={email}
              onChangeText={setEmail}
            />
          </View>
        </View>

        <View className="mb-2">
          <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Password
          </Text>
          <View className="flex-row items-center border border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900 px-4 py-3">
            <Feather name="lock" size={20} color={colorScheme === 'dark' ? '#9ca3af' : '#6b7280'} />
            <TextInput
              className="flex-1 ml-3 text-base text-gray-900 dark:text-white"
              placeholder="Enter your password"
              placeholderTextColor={colorScheme === 'dark' ? '#6b7280' : '#9ca3af'}
              secureTextEntry={!showPassword}
              value={password}
              onChangeText={setPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
              <Feather
                name={showPassword ? 'eye-off' : 'eye'}
                size={20}
                color={colorScheme === 'dark' ? '#9ca3af' : '#6b7280'}
              />
            </TouchableOpacity>
          </View>
        </View>

        <View className="items-end mb-8">
          <TouchableOpacity onPress={() => router.push('/(auth)/forgot-password')}>
            <Text className="text-blue-500 font-semibold">Forgot Password?</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          className="bg-blue-500 rounded-xl py-4 items-center justify-center mb-6 shadow-sm"
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-bold text-lg">Sign In</Text>
          )}
        </TouchableOpacity>

        <View className="flex-row justify-center items-center">
          <Text className="text-gray-600 dark:text-gray-400">Don't have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/(auth)/register')}>
            <Text className="text-blue-500 font-bold text-base">Sign Up</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
