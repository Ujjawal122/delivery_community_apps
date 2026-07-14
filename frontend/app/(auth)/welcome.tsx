import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import Animated, {
  FadeInDown,
  FadeInUp,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  withSpring,
  Easing,
} from 'react-native-reanimated';
import { Ionicons, Feather } from '@expo/vector-icons';
import { useTheme } from '../../constants/theme';
import ThemeToggle from '../../components/ThemeToggle';

const { width } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const theme = useTheme();

  // Floating truck animation
  const floatY = useSharedValue(0);
  const logoScale = useSharedValue(0.8);

  useEffect(() => {
    // Continuous float loop
    floatY.value = withRepeat(
      withSequence(
        withTiming(-12, { duration: 1400, easing: Easing.inOut(Easing.sin) }),
        withTiming(0, { duration: 1400, easing: Easing.inOut(Easing.sin) })
      ),
      -1,
      true
    );
    // Entrance scale
    logoScale.value = withSpring(1, { damping: 10, stiffness: 120 });
  }, []);

  const floatStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: floatY.value }, { scale: logoScale.value }],
  }));

  const buttonScale = useSharedValue(1);
  const onPressIn = () => {
    buttonScale.value = withSpring(0.96, { damping: 10 });
  };
  const onPressOut = () => {
    buttonScale.value = withSpring(1, { damping: 10 });
  };
  const btnStyle = useAnimatedStyle(() => ({ transform: [{ scale: buttonScale.value }] }));

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      {/* Theme Toggle top-right */}
      <View style={styles.topBar}>
        <ThemeToggle />
      </View>

      {/* Decorative circles */}
      <View
        style={[
          styles.circle1,
          { backgroundColor: theme.isDark ? '#1E3A8A' : '#DBEAFE', opacity: 0.5 },
        ]}
      />
      <View
        style={[
          styles.circle2,
          { backgroundColor: theme.isDark ? '#172554' : '#EFF6FF', opacity: 0.4 },
        ]}
      />

      {/* Hero Section */}
      <View style={styles.hero}>
        {/* Animated Logo Icon */}
        <Animated.View style={[floatStyle, styles.logoWrapper]}>
          <View
            style={[
              styles.logoBox,
              {
                backgroundColor: theme.accent,
                shadowColor: theme.accent,
              },
            ]}
          >
            <Feather name="truck" size={52} color="#FFFFFF" />
          </View>
          {/* Shadow below logo */}
          <View
            style={[
              styles.logoShadow,
              { backgroundColor: theme.isDark ? '#60A5FA' : '#2563EB', opacity: 0.2 },
            ]}
          />
        </Animated.View>

        {/* App name with staggered FadeInUp */}
        <Animated.Text
          entering={FadeInUp.delay(200).duration(700).springify()}
          style={[styles.appName, { color: theme.textPrimary }]}
        >
          Delivery Community
        </Animated.Text>

        <Animated.Text
          entering={FadeInUp.delay(350).duration(700).springify()}
          style={[styles.tagline, { color: theme.textSecondary }]}
        >
          Connect, share tips & grow{'\n'}with fellow delivery drivers.
        </Animated.Text>

        {/* Feature badges */}
        <Animated.View
          entering={FadeInUp.delay(500).duration(600)}
          style={styles.badges}
        >
          {[
            { icon: 'warning', label: 'Hazard Map' },
            { icon: 'people', label: 'Community' },
            { icon: 'chatbubbles', label: 'Real-time Chat' },
          ].map((item) => (
            <View
              key={item.label}
              style={[
                styles.badge,
                {
                  backgroundColor: theme.bgSubtle,
                  borderColor: theme.border,
                },
              ]}
            >
              <Ionicons name={item.icon as any} size={14} color={theme.accent} />
              <Text style={[styles.badgeText, { color: theme.textSecondary }]}>
                {item.label}
              </Text>
            </View>
          ))}
        </Animated.View>
      </View>

      {/* CTA Buttons */}
      <Animated.View
        entering={FadeInDown.delay(400).duration(700).springify()}
        style={styles.buttons}
      >
        <Animated.View style={btnStyle}>
          <TouchableOpacity
            onPress={() => router.push('/(auth)/login')}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            style={[styles.primaryBtn, { backgroundColor: theme.accent }]}
            activeOpacity={1}
          >
            <Text style={styles.primaryBtnText}>Sign In</Text>
            <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 8 }} />
          </TouchableOpacity>
        </Animated.View>

        <TouchableOpacity
          onPress={() => router.push('/(auth)/register')}
          style={[
            styles.secondaryBtn,
            { backgroundColor: theme.bgSubtle, borderColor: theme.border },
          ]}
          activeOpacity={0.8}
        >
          <Text style={[styles.secondaryBtnText, { color: theme.textPrimary }]}>
            Create Account
          </Text>
        </TouchableOpacity>

        <Text style={[styles.footer, { color: theme.textMuted }]}>
          Join thousands of delivery workers today
        </Text>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 28,
    paddingVertical: 60,
  },
  topBar: {
    position: 'absolute',
    top: 56,
    right: 24,
    zIndex: 10,
  },
  circle1: {
    position: 'absolute',
    width: width * 0.8,
    height: width * 0.8,
    borderRadius: width * 0.4,
    top: -width * 0.2,
    right: -width * 0.2,
  },
  circle2: {
    position: 'absolute',
    width: width * 0.6,
    height: width * 0.6,
    borderRadius: width * 0.3,
    bottom: -width * 0.1,
    left: -width * 0.2,
  },
  hero: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  logoWrapper: {
    alignItems: 'center',
    marginBottom: 8,
  },
  logoBox: {
    width: 96,
    height: 96,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 10,
  },
  logoShadow: {
    width: 60,
    height: 10,
    borderRadius: 30,
    marginTop: 8,
  },
  appName: {
    fontSize: 34,
    fontWeight: '800',
    textAlign: 'center',
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
  badges: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  buttons: {
    width: '100%',
    gap: 12,
    alignItems: 'center',
  },
  primaryBtn: {
    width: width - 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 16,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 17,
  },
  secondaryBtn: {
    width: width - 56,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 16,
    borderWidth: 1.5,
  },
  secondaryBtnText: {
    fontWeight: '700',
    fontSize: 17,
  },
  footer: {
    fontSize: 13,
    marginTop: 4,
  },
});

