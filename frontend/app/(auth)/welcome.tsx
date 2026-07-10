import { View, Text, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';

export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <View className="flex-1 bg-white dark:bg-slate-900 justify-center items-center px-6">
      <Animated.View entering={FadeInUp.duration(1000).springify()} className="items-center mb-12">
        <View className="w-24 h-24 bg-blue-500 rounded-3xl mb-6 shadow-lg shadow-blue-500/50 justify-center items-center">
          <Text className="text-white text-4xl font-bold">D</Text>
        </View>
        <Text className="text-4xl font-extrabold text-slate-900 dark:text-white mb-3 text-center">
          Delivery Community
        </Text>
        <Text className="text-lg text-slate-500 dark:text-slate-400 text-center">
          Connect, share tips, and grow with fellow delivery drivers.
        </Text>
      </Animated.View>

      <Animated.View entering={FadeInDown.duration(1000).delay(300).springify()} className="w-full space-y-4">
        <TouchableOpacity
          onPress={() => router.push('/(auth)/login')}
          className="w-full bg-blue-600 rounded-2xl py-4 items-center shadow-lg shadow-blue-600/30"
        >
          <Text className="text-white font-bold text-lg">Login</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push('/(auth)/register')}
          className="w-full bg-slate-100 dark:bg-slate-800 rounded-2xl py-4 items-center mt-4"
        >
          <Text className="text-slate-900 dark:text-white font-bold text-lg">Create Account</Text>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
}
