import { create } from 'zustand';

export interface User {
  id: string;
  full_name: string;
  avatar: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string | null;
  content: string;
  is_system_message: boolean;
  created_at: string;
  sender: User | null;
}

export interface ConversationMember {
  id: string;
  user_id: string;
  last_read_at: string;
  user: User;
}

export interface Conversation {
  id: string;
  type: 'direct' | 'community';
  members: ConversationMember[];
  latest_message: Message | null;
  updated_at: string;
  unread_count?: number;
}

interface ChatState {
  conversations: Conversation[];
  messages: Record<string, Message[]>; // conversation_id -> messages
  onlineUsers: Set<string>;
  typingUsers: Record<string, Set<string>>; // conversation_id -> Set of user_ids
  unreadChatCount: number;
  activeConversationId: string | null;
  
  setActiveConversation: (id: string | null) => void;
  markConversationAsRead: (id: string) => void;
  
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  setMessages: (conversationId: string, messages: Message[]) => void;
  addMessage: (message: Message) => void;
  
  setOnlineStatus: (userId: string, isOnline: boolean) => void;
  setTypingStatus: (conversationId: string, userId: string) => void;
  setUnreadChatCount: (count: number) => void;
  incrementUnreadChatCount: () => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  messages: {},
  onlineUsers: new Set(),
  typingUsers: {},
  unreadChatCount: 0,
  activeConversationId: null,

  setActiveConversation: (id) => set({ activeConversationId: id }),

  markConversationAsRead: (id) => set((state) => {
    const updatedConversations = state.conversations.map(c => 
      c.id === id ? { ...c, unread_count: 0 } : c
    );
    return { conversations: updatedConversations };
  }),

  setConversations: (conversations) => set({ conversations }),
  
  setUnreadChatCount: (count) => set({ unreadChatCount: count }),
  incrementUnreadChatCount: () => set((state) => ({ unreadChatCount: state.unreadChatCount + 1 })),
  reset: () => set({
    conversations: [],
    messages: {},
    onlineUsers: new Set(),
    typingUsers: {},
    unreadChatCount: 0,
    activeConversationId: null,
  }),

  addConversation: (conversation) => set((state) => {    const exists = state.conversations.find((c) => c.id === conversation.id);
    if (exists) return state;
    return { conversations: [conversation, ...state.conversations] };
  }),

  setMessages: (conversationId, messages) => set((state) => ({
    messages: {
      ...state.messages,
      [conversationId]: messages
    }
  })),

  addMessage: (message) => set((state) => {
    const convoMessages = state.messages[message.conversation_id] || [];
    
    // Deduplicate to avoid duplicate keys in FlatList
    if (convoMessages.some(m => m.id === message.id)) {
      return state;
    }

    // Update the latest_message and unread_count in conversations as well
    const updatedConversations = state.conversations.map(c => {
      if (c.id === message.conversation_id) {
        // Increment unread count if it's not the active conversation and not sent by me
        // For simplicity, just check if it's not the active conversation
        const isNotActive = state.activeConversationId !== message.conversation_id;
        // Check if the current user is NOT the sender. We don't want to increment for our own messages.
        // We don't have direct access to current user ID here, but normally backend websocket doesn't echo our own messages back as 'new_message', except in this case maybe?
        // Actually, we can just increment if isNotActive. 
        const newUnreadCount = isNotActive ? (c.unread_count || 0) + 1 : 0;
        
        return { 
          ...c, 
          latest_message: message, 
          updated_at: message.created_at,
          unread_count: newUnreadCount 
        };
      }
      return c;
    }).sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

    return {
      messages: {
        ...state.messages,
        [message.conversation_id]: [message, ...convoMessages] // prepend because newest is first
      },
      conversations: updatedConversations
    };
  }),

  setOnlineStatus: (userId, isOnline) => set((state) => {
    const newOnline = new Set(state.onlineUsers);
    if (isOnline) {
      newOnline.add(userId);
    } else {
      newOnline.delete(userId);
    }
    return { onlineUsers: newOnline };
  }),

  setTypingStatus: (conversationId, userId) => {
    set((state) => {
      const currentTyping = state.typingUsers[conversationId] || new Set();
      const newTyping = new Set(currentTyping);
      newTyping.add(userId);
      return {
        typingUsers: {
          ...state.typingUsers,
          [conversationId]: newTyping
        }
      };
    });
    
    // Auto remove typing status after 3 seconds
    setTimeout(() => {
      set((state) => {
        const currentTyping = state.typingUsers[conversationId];
        if (!currentTyping) return state;
        const newTyping = new Set(currentTyping);
        newTyping.delete(userId);
        return {
          typingUsers: {
            ...state.typingUsers,
            [conversationId]: newTyping
          }
        };
      });
    }, 3000);
  }
}));
