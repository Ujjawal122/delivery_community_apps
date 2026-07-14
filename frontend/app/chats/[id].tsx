import React, { useEffect, useState, useRef } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, FlatList, 
  KeyboardAvoidingView, Platform, ActivityIndicator 
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useColorScheme } from 'nativewind';
import apiClient from '../api/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useChatStore, Message } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import { useWebSocket } from '../../services/useWebSocket';


const EMPTY_MESSAGES: Message[] = [];
const EMPTY_SET = new Set<string>();

export default function ChatRoomScreen() {
  const { id } = useLocalSearchParams();
  const conversationId = Array.isArray(id) ? id[0] : id;
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  const { colorScheme } = useColorScheme();
  const isDark = colorScheme === 'dark';


  const currentUser = useAuthStore((state) => state.user);

  const messages = useChatStore((state) => state.messages[conversationId] || EMPTY_MESSAGES);
  const setMessages = useChatStore((state) => state.setMessages);
  const addMessage = useChatStore((state) => state.addMessage);
  const typingUsers = useChatStore((state) => state.typingUsers[conversationId] || EMPTY_SET);
  const conversations = useChatStore((state) => state.conversations);
  
  const { sendTyping } = useWebSocket();

  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(true);
  const flatListRef = useRef<FlatList>(null);

  // Find the other user to display their name
  const conversation = conversations.find(c => c.id === conversationId);
  const otherMember = conversation?.members.find(m => m.user_id !== currentUser?.id);
  const otherUser = otherMember?.user;
  
  const onlineUsers = useChatStore((state) => state.onlineUsers);
  const isOnline = otherUser && onlineUsers.has(otherUser.id);
  const isTyping = typingUsers.size > 0 && Array.from(typingUsers).some(userId => userId !== currentUser?.id);

  useEffect(() => {
    fetchMessages();
  }, [conversationId]);

  const fetchMessages = async () => {
    try {
      const res = await apiClient.get(`/chat/conversations/${conversationId}/messages`);
      // The API returns them in chronological order. Our flat list uses inverted={true} so we need them reversed.
      // Or we can just set them directly if the store handles it.
      // Wait, FlatList inverted expects newest first.
      const reversed = [...res.data].reverse();
      setMessages(conversationId, reversed);
    } catch (error) {
      console.error('Failed to load messages', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;
    
    const textToSend = inputText.trim();
    setInputText('');

    try {
      const res = await apiClient.post(
        `/chat/conversations/${conversationId}/messages`,
        { content: textToSend }
      );
      // addMessage(res.data); // Actually, we might receive it via WS too.
      // To avoid duplicates, we can rely on WS or add it here and deduplicate.
      // For now, adding it immediately gives better UX.
      addMessage(res.data);
    } catch (error) {
      console.error('Failed to send message', error);
      // Ideally show an error toast
    }
  };

  const handleTextChange = (text: string) => {
    setInputText(text);
    sendTyping(conversationId);
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isMe = Boolean(
      currentUser?.id && 
      (String(item.sender_id).toLowerCase() === String(currentUser.id).toLowerCase() ||
       String(item.sender?.id).toLowerCase() === String(currentUser.id).toLowerCase())
    );
    
    return (
      <View style={{ flexDirection: 'row', justifyContent: isMe ? 'flex-end' : 'flex-start' }} className="my-1 mx-2">
        <View className={`max-w-[80%] px-3 py-2 ${
          isMe 
            ? 'bg-[#E1FFC7] dark:bg-[#005C4B] rounded-2xl rounded-tr-sm' 
            : 'bg-white dark:bg-slate-800 rounded-2xl rounded-tl-sm'
        }`} style={{ shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 1, elevation: 1 }}>
          <Text className={`text-[15px] ${isMe ? 'text-black dark:text-white' : 'text-slate-900 dark:text-white'}`}>
            {item.content}
          </Text>
          <Text className={`text-[10px] mt-1 self-end ${
            isMe ? 'text-slate-500 dark:text-slate-300' : 'text-slate-500 dark:text-slate-400'
          }`}>
            {new Date(item.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView 
      className={`flex-1 ${isDark ? 'bg-slate-900' : 'bg-white'}`}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Header */}
      <View 
        className={`flex-row items-center px-4 pb-4 border-b ${isDark ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-white'}`}
        style={{ paddingTop: insets.top + 10 }}
      >
        <TouchableOpacity onPress={() => router.back()} className="mr-4">
          <Ionicons name="arrow-back" size={24} color={isDark ? 'white' : 'black'} />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            {otherUser ? otherUser.full_name : 'Chat'}
          </Text>
          {isTyping ? (
            <Text className={`text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
              typing...
            </Text>
          ) : (
            <Text className={`text-xs ${isOnline ? (isDark ? 'text-green-400' : 'text-green-600') : (isDark ? 'text-slate-500' : 'text-slate-500')}`}>
              {isOnline ? 'Online' : 'Offline'}
            </Text>
          )}
        </View>
      </View>

      {/* Messages */}
      {loading ? (
        <View className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          inverted
          contentContainerStyle={{ paddingVertical: 16 }}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Input Area */}
      <View 
        className={`flex-row items-center px-4 py-2 border-t ${isDark ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-white'}`}
        style={{ paddingBottom: Math.max(insets.bottom, 16) }}
      >
        <View className={`flex-1 flex-row items-center rounded-full px-4 py-2 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}>
          <TextInput
            className={`flex-1 max-h-32 text-base ${isDark ? 'text-white' : 'text-slate-900'}`}
            placeholder="Type a message..."
            placeholderTextColor={isDark ? '#94A3B8' : '#64748B'}
            multiline
            value={inputText}
            onChangeText={handleTextChange}
          />
        </View>
        <TouchableOpacity 
          className={`ml-3 w-10 h-10 rounded-full items-center justify-center ${inputText.trim() ? 'bg-blue-500' : isDark ? 'bg-slate-800' : 'bg-slate-200'}`}
          onPress={handleSend}
          disabled={!inputText.trim()}
        >
          <Ionicons 
            name="send" 
            size={18} 
            color={inputText.trim() ? 'white' : isDark ? '#475569' : '#94A3B8'} 
            style={{ marginLeft: 2 }} // Optical alignment for send icon
          />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
