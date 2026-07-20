if (typeof globalThis.DOMException === 'undefined') {
  class DOMException extends Error {
    code: number;
    constructor(message?: string, name?: string) {
      super(message);
      this.name = name ?? 'Error';
      this.code = 0;
    }
  }
  (globalThis as any).DOMException = DOMException;
}

import { useFonts } from 'expo-font';
import { DarkTheme, DefaultTheme, Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import 'react-native-reanimated';
import '../global.css';
import { useColorScheme } from 'nativewind';
import { useAuthStore } from '../store/authStore';
import { useChatStore } from '../store/chatStore';
import { useWebSocket } from '../services/useWebSocket';
import '../services/locationTracking';

export {
  // Catch any errors thrown by the Layout component.
  ErrorBoundary,
} from 'expo-router';

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
  });

  const { checkAuth, isLoading, isAuthenticated } = useAuthStore();
  const [authInitialized, setAuthInitialized] = useState(false);

  useEffect(() => {
    if (error) throw error;
  }, [error]);

  useEffect(() => {
    // Run the auth check
    checkAuth().finally(() => {
      setAuthInitialized(true);
    });
  }, []);

  useEffect(() => {
    if (loaded && authInitialized) {
      SplashScreen.hideAsync();
    }
  }, [loaded, authInitialized]);

  if (!loaded || !authInitialized) {
    return null;
  }

  return <RootLayoutNav />;
}

function RootLayoutNav() {
  const { colorScheme } = useColorScheme();
  const { isAuthenticated } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();
  
  const { disconnect } = useWebSocket();

  useEffect(() => {
    const inAuthGroup = segments[0] === '(auth)';
    
    if (isAuthenticated && inAuthGroup) {
      // If user is authenticated and trying to access auth screens, send to tabs
      router.replace('/(tabs)');
    } else if (!isAuthenticated && !inAuthGroup) {
      // If user is NOT authenticated and trying to access app, send to auth
      disconnect(); // Disconnect websocket when logging out
      useChatStore.getState().reset(); // Clear chat state for next login
      router.replace('/(auth)/welcome');
    }
  }, [isAuthenticated, segments]);

  return (
    <Stack screenOptions={{ headerShown: false, animation: 'fade' }}>
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="post/[id]" />
      <Stack.Screen name="create" options={{ presentation: 'modal' }} />
    </Stack>
  );
}
