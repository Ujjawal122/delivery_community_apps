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
import apiClient from '../api/client';
import { useColorScheme } from 'nativewind';

export default function RegisterScreen() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const router = useRouter();
  const { colorScheme } = useColorScheme();

  const handleRegister = async () => {
    if (!fullName || !email || !password) {
      setError('Please fill in all fields');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiClient.post('/auth/register', {
        full_name: fullName,
        email,
        password,
      });

      if (response.data.success) {
        setSuccess('Registration successful! Please login to continue.');
        setTimeout(() => {
          router.replace('/(auth)/login');
        }, 2000);
      } else {
        setError(response.data.message || 'Registration failed');
      }
    } catch (err: any) {
      setError(
        err.response?.data?.message || 'An error occurred during registration. Please try again.'
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
        <View className="mb-8 items-center">
          <View className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-full mb-4">
            <Feather name="user-plus" size={48} color="#3b82f6" />
          </View>
          <Text className="text-3xl font-bold text-gray-900 dark:text-white mb-2 text-center">
            Create Account
          </Text>
          <Text className="text-base text-gray-500 dark:text-gray-400 text-center">
            Join the Delivery Community today
          </Text>
        </View>

        {error ? (
          <View className="bg-red-100 border-l-4 border-red-500 p-4 mb-6 rounded-r-md">
            <Text className="text-red-700">{error}</Text>
          </View>
        ) : null}

        {success ? (
          <View className="bg-green-100 border-l-4 border-green-500 p-4 mb-6 rounded-r-md">
            <Text className="text-green-700">{success}</Text>
          </View>
        ) : null}

        <View className="mb-5">
          <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Full Name
          </Text>
          <View className="flex-row items-center border border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900 px-4 py-3">
            <Feather name="user" size={20} color={colorScheme === 'dark' ? '#9ca3af' : '#6b7280'} />
            <TextInput
              className="flex-1 ml-3 text-base text-gray-900 dark:text-white"
              placeholder="Enter your full name"
              placeholderTextColor={colorScheme === 'dark' ? '#6b7280' : '#9ca3af'}
              autoCapitalize="words"
              value={fullName}
              onChangeText={setFullName}
            />
          </View>
        </View>

        <View className="mb-5">
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

        <View className="mb-8">
          <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Password
          </Text>
          <View className="flex-row items-center border border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900 px-4 py-3">
            <Feather name="lock" size={20} color={colorScheme === 'dark' ? '#9ca3af' : '#6b7280'} />
            <TextInput
              className="flex-1 ml-3 text-base text-gray-900 dark:text-white"
              placeholder="Create a password (min 8 chars)"
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

        <TouchableOpacity
          className="bg-blue-500 rounded-xl py-4 items-center justify-center mb-6 shadow-sm"
          onPress={handleRegister}
          disabled={loading || !!success}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-bold text-lg">Sign Up</Text>
          )}
        </TouchableOpacity>

        <View className="flex-row justify-center items-center">
          <Text className="text-gray-600 dark:text-gray-400">Already have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/(auth)/login')}>
            <Text className="text-blue-500 font-bold text-base">Sign In</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
