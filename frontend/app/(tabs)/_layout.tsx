import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useColorScheme } from 'nativewind';
import { Platform } from 'react-native';

export default function TabLayout() {
  const { colorScheme } = useColorScheme();
  
  const isDark = colorScheme === 'dark';
  const activeColor = isDark ? '#60A5FA' : '#2563EB'; // blue-400 : blue-600
  const inactiveColor = isDark ? '#64748B' : '#94A3B8'; // slate-500 : slate-400
  const backgroundColor = isDark ? '#0F172A' : '#FFFFFF'; // slate-900 : white

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: activeColor,
        tabBarInactiveTintColor: inactiveColor,
        tabBarStyle: {
          backgroundColor: backgroundColor,
          borderTopColor: isDark ? '#1E293B' : '#E2E8F0',
          paddingBottom: Platform.OS === 'ios' ? 20 : 10,
          height: Platform.OS === 'ios' ? 88 : 64,
        },
        tabBarShowLabel: false,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Feed',
          tabBarIcon: ({ color }) => <Ionicons name="home" size={26} color={color} />,
        }}
      />
      <Tabs.Screen
        name="bookmarks"
        options={{
          title: 'Bookmarks',
          tabBarIcon: ({ color }) => <Ionicons name="bookmark" size={26} color={color} />,
        }}
      />
      <Tabs.Screen
        name="communities"
        options={{
          title: 'Communities',
          tabBarIcon: ({ color }) => <Ionicons name="people" size={26} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => <Ionicons name="person" size={26} color={color} />,
        }}
      />
      <Tabs.Screen
        name="locations"
        options={{
          title: 'Hazards & Gates',
          tabBarIcon: ({ color }) => <Ionicons name="location" size={26} color={color} />,
        }}
      />
    </Tabs>
  );
}
