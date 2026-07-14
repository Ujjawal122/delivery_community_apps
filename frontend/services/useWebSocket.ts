import { useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useChatStore } from '../store/chatStore';


// For Android Emulator:  'ws://10.0.2.2:8000/chat/ws'
// For Physical Device:   use your PC's local Wi-Fi IP
const WS_URL = 'ws://10.0.2.2:8000/chat/ws';


export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);

  
  const addMessage = useChatStore((state) => state.addMessage);
  const setOnlineStatus = useChatStore((state) => state.setOnlineStatus);
  const setTypingStatus = useChatStore((state) => state.setTypingStatus);

  useEffect(() => {
    const connectWs = async () => {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return;

      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log('WebSocket Connected');
        ws.current?.send(JSON.stringify({ type: 'auth', token }));
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'new_message':
              addMessage(data.message);
              // Optimistically increment unread chat count if not in chat screen
              // (In a real app, you'd check if the user is currently viewing this conversation)
              useChatStore.getState().incrementUnreadChatCount();
              break;
            case 'status':
              setOnlineStatus(data.user_id, data.status === 'online');
              break;
            case 'typing':
              setTypingStatus(data.conversation_id, data.user_id);
              break;
            case 'new_notification':
              import('../store/notificationStore').then(({ useNotificationStore }) => {
                useNotificationStore.getState().addNotification(data.notification);
                useNotificationStore.getState().incrementUnreadCount();
              });
              break;
            case 'unread_count_update':
              import('../store/notificationStore').then(({ useNotificationStore }) => {
                useNotificationStore.getState().updateUnreadCount(data.unread_count);
              });
              break;
            case 'chat_unread_count_update':
              useChatStore.getState().setUnreadChatCount(data.unread_count);
              break;
          }
        } catch (error) {
          console.error('Error parsing WS message', error);
        }
      };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
    };

    };

    connectWs();

    return () => {
      ws.current?.close();
    };
  }, []);

  const sendMessage = (conversationId: string, content: string) => {
    // Actually our backend doesn't support sending messages via WS directly in this implementation,
    // we use REST POST for messages. But we can send typing indicators.
  };

  const sendTyping = (conversationId: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'typing',
        conversation_id: conversationId
      }));
    }
  };

  return { sendTyping };
}
