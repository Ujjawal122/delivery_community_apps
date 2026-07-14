import React, { useCallback } from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useColorScheme } from 'nativewind';
import { useTheme } from '../constants/theme';

interface ThemeToggleProps {
  size?: number;
}

export default function ThemeToggle({ size = 24 }: ThemeToggleProps) {
  const { colorScheme, setColorScheme } = useColorScheme();
  const theme = useTheme();
  const isDark = colorScheme === 'dark';

  // Rotation shared value: 0 = sun (light), 1 = moon (dark)
  const rotation = useSharedValue(isDark ? 1 : 0);
  const scale = useSharedValue(1);

  const handleToggle = useCallback(() => {
    const next = isDark ? 'light' : 'dark';
    // Spin + bounce animation
    rotation.value = withSpring(isDark ? 0 : 1, { damping: 12, stiffness: 180 });
    scale.value = withSpring(0.8, { damping: 8 }, () => {
      scale.value = withSpring(1, { damping: 10, stiffness: 200 });
    });
    setColorScheme(next);
  }, [isDark, setColorScheme]);

  const animatedStyle = useAnimatedStyle(() => {
    const rotate = interpolate(rotation.value, [0, 1], [0, 360], Extrapolation.CLAMP);
    return {
      transform: [
        { rotate: `${rotate}deg` },
        { scale: scale.value },
      ],
    };
  });

  return (
    <TouchableOpacity
      onPress={handleToggle}
      activeOpacity={0.7}
      style={[
        styles.container,
        {
          backgroundColor: isDark ? '#1E293B' : '#F1F5F9',
          borderColor: isDark ? '#334155' : '#E2E8F0',
        },
      ]}
    >
      <Animated.View style={animatedStyle}>
        <Ionicons
          name={isDark ? 'moon' : 'sunny'}
          size={size}
          color={isDark ? '#60A5FA' : '#F59E0B'}
        />
      </Animated.View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
