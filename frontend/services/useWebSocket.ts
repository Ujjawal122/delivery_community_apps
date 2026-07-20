import { useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useChatStore } from '../store/chatStore';


// For Android Emulator:  'ws://10.0.2.2:8000/chat/ws'
// For Physical Device:   use your PC's local Wi-Fi IP
const WS_URL = 'ws://10.0.2.2:8000/chat/ws';


let globalWs: WebSocket | null = null;

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);

  const addMessage = useChatStore((state) => state.addMessage);
  const setOnlineStatus = useChatStore((state) => state.setOnlineStatus);
  const setTypingStatus = useChatStore((state) => state.setTypingStatus);

  useEffect(() => {
    const connectWs = async () => {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        if (globalWs) {
          globalWs.close();
          globalWs = null;
        }
        return;
      }

      if (globalWs && (globalWs.readyState === WebSocket.OPEN || globalWs.readyState === WebSocket.CONNECTING)) {
        ws.current = globalWs;
        return;
      }

      const newWs = new WebSocket(WS_URL);
      globalWs = newWs;
      ws.current = newWs;

      newWs.onopen = () => {
        console.log('WebSocket Connected');
        newWs.send(JSON.stringify({ type: 'auth', token }));
      };

      newWs.onmessage = (event) => {
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

      newWs.onerror = (error) => {
        console.log('WebSocket Error:', error);
      };

      newWs.onclose = () => {
        console.log('WebSocket Disconnected');
        if (globalWs === newWs) {
          globalWs = null;
        }
      };
    };

    connectWs();

    // Do NOT close globalWs on unmount, otherwise navigating between screens kills the socket
  }, []);

  const sendMessage = (conversationId: string, content: string) => {
    // Actually our backend doesn't support sending messages via WS directly in this implementation,
    // we use REST POST for messages. But we can send typing indicators.
  };

  const sendTyping = (conversationId: string) => {
    if (globalWs?.readyState === WebSocket.OPEN) {
      globalWs.send(JSON.stringify({
        type: 'typing',
        conversation_id: conversationId
      }));
    }
  };

  const disconnect = () => {
    if (globalWs) {
      globalWs.close();
      globalWs = null;
    }
  };

  return { sendTyping, disconnect };
}
