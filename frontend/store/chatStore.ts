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
}

interface ChatState {
  conversations: Conversation[];
  messages: Record<string, Message[]>; // conversation_id -> messages
  onlineUsers: Set<string>;
  typingUsers: Record<string, Set<string>>; // conversation_id -> Set of user_ids
  unreadChatCount: number;
  
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  setMessages: (conversationId: string, messages: Message[]) => void;
  addMessage: (message: Message) => void;
  
  setOnlineStatus: (userId: string, isOnline: boolean) => void;
  setTypingStatus: (conversationId: string, userId: string) => void;
  setUnreadChatCount: (count: number) => void;
  incrementUnreadChatCount: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  messages: {},
  onlineUsers: new Set(),
  typingUsers: {},
  unreadChatCount: 0,

  setConversations: (conversations) => set({ conversations }),
  
  setUnreadChatCount: (count) => set({ unreadChatCount: count }),
  incrementUnreadChatCount: () => set((state) => ({ unreadChatCount: state.unreadChatCount + 1 })),

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

    // Update the latest_message in conversations as well
    const updatedConversations = state.conversations.map(c => 
      c.id === message.conversation_id 
        ? { ...c, latest_message: message, updated_at: message.created_at } 
        : c
    ).sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

    return {
      messages: {
        ...state.messages,
        [message.conversation_id]: [message, ...convoMessages] // prepend
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
