import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
} from 'react-native';
import Animated, {
  FadeInDown,
  FadeInUp,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  interpolateColor,
} from 'react-native-reanimated';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import apiClient from '../api/client';
import { useTheme } from '../../constants/theme';
import ThemeToggle from '../../components/ThemeToggle';

const { width } = Dimensions.get('window');

// ── Animated Input Field ───────────────────────────────────────────────────
function AnimatedInput({
  icon,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  keyboardType,
  autoCapitalize,
  rightElement,
  theme,
}: any) {
  const focus = useSharedValue(0);
  const [isFocused, setIsFocused] = React.useState(false);

  const containerStyle = useAnimatedStyle(() => ({
    borderColor: interpolateColor(focus.value, [0, 1], [theme.border, theme.accent]),
    transform: [{ scale: withSpring(focus.value === 1 ? 1.01 : 1, { damping: 15 }) }],
  }));

  return (
    <Animated.View
      style={[
        styles.inputContainer,
        { backgroundColor: theme.bgSubtle },
        containerStyle,
      ]}
    >
      <Feather name={icon} size={18} color={isFocused ? theme.accent : theme.textMuted} style={styles.inputIcon} />
      <TextInput
        style={[styles.input, { color: theme.textPrimary }]}
        placeholder={placeholder}
        placeholderTextColor={theme.textMuted}
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry}
        keyboardType={keyboardType}
        autoCapitalize={autoCapitalize ?? 'none'}
        onFocus={() => {
          focus.value = withTiming(1, { duration: 200 });
          setIsFocused(true);
        }}
        onBlur={() => {
          focus.value = withTiming(0, { duration: 200 });
          setIsFocused(false);
        }}
      />
      {rightElement}
    </Animated.View>
  );
}

// ── Login Screen ───────────────────────────────────────────────────────────
export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const router = useRouter();
  const { login } = useAuthStore();
  const theme = useTheme();

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      if (response.data.success) {
        const { access_token, refresh_token, user } = response.data.data;
        await login(access_token, refresh_token, user);
      } else {
        setError(response.data.message || 'Login failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const btnScale = useSharedValue(1);
  const btnStyle = useAnimatedStyle(() => ({ transform: [{ scale: btnScale.value }] }));

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.root, { backgroundColor: theme.bg }]}
    >
      {/* Top bar with theme toggle */}
      <View style={[styles.topBar, { backgroundColor: theme.bg }]}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={theme.textPrimary} />
        </TouchableOpacity>
        <ThemeToggle />
      </View>

      <ScrollView
        contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 24, paddingTop: 80 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <Animated.View entering={FadeInDown.delay(100).duration(600).springify()} style={styles.header}>
          <View style={[styles.iconBox, { backgroundColor: theme.accentLight }]}>
            <Feather name="truck" size={40} color={theme.accent} />
          </View>
          <Text style={[styles.title, { color: theme.textPrimary }]}>Welcome Back</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Sign in to Delivery Community
          </Text>
        </Animated.View>

        {/* Error Banner */}
        {error ? (
          <Animated.View
            entering={FadeInDown.duration(300)}
            style={[styles.errorBanner, { backgroundColor: '#FEE2E2', borderLeftColor: '#EF4444' }]}
          >
            <Ionicons name="alert-circle" size={16} color="#EF4444" />
            <Text style={styles.errorText}>{error}</Text>
          </Animated.View>
        ) : null}

        {/* Form */}
        <Animated.View entering={FadeInDown.delay(200).duration(600).springify()} style={styles.form}>
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>Email Address</Text>
            <AnimatedInput
              icon="mail"
              placeholder="Enter your email"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              theme={theme}
            />
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>Password</Text>
            <AnimatedInput
              icon="lock"
              placeholder="Enter your password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              theme={theme}
              rightElement={
                <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeBtn}>
                  <Feather
                    name={showPassword ? 'eye-off' : 'eye'}
                    size={18}
                    color={theme.textMuted}
                  />
                </TouchableOpacity>
              }
            />
          </View>

          <TouchableOpacity
            onPress={() => router.push('/(auth)/forgot-password')}
            style={styles.forgotRow}
          >
            <Text style={[styles.forgotText, { color: theme.accent }]}>Forgot Password?</Text>
          </TouchableOpacity>
        </Animated.View>

        {/* CTA */}
        <Animated.View entering={FadeInDown.delay(350).duration(600).springify()}>
          <Animated.View style={btnStyle}>
            <TouchableOpacity
              style={[styles.loginBtn, { backgroundColor: theme.accent, opacity: loading ? 0.8 : 1 }]}
              onPress={handleLogin}
              onPressIn={() => { btnScale.value = withSpring(0.97, { damping: 10 }); }}
              onPressOut={() => { btnScale.value = withSpring(1, { damping: 10 }); }}
              disabled={loading}
              activeOpacity={1}
            >
              {loading ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <>
                  <Text style={styles.loginBtnText}>Sign In</Text>
                  <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 8 }} />
                </>
              )}
            </TouchableOpacity>
          </Animated.View>

          <View style={styles.signupRow}>
            <Text style={[styles.signupLabel, { color: theme.textSecondary }]}>
              Don't have an account?{'  '}
            </Text>
            <TouchableOpacity onPress={() => router.push('/(auth)/register')}>
              <Text style={[styles.signupLink, { color: theme.accent }]}>Sign Up</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  topBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 56 : 40,
    paddingBottom: 12,
    zIndex: 10,
  },
  header: { alignItems: 'center', marginBottom: 28 },
  iconBox: {
    width: 72,
    height: 72,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: { fontSize: 28, fontWeight: '800', letterSpacing: -0.5, marginBottom: 6 },
  subtitle: { fontSize: 15, textAlign: 'center' },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderLeftWidth: 4,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: { color: '#B91C1C', flex: 1, fontSize: 14 },
  form: { gap: 16, marginBottom: 12 },
  field: { gap: 6 },
  label: { fontSize: 13, fontWeight: '600', marginLeft: 4 },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 14,
    gap: 10,
  },
  inputIcon: { width: 20 },
  input: { flex: 1, fontSize: 15 },
  eyeBtn: { padding: 4 },
  forgotRow: { alignItems: 'flex-end' },
  forgotText: { fontSize: 13, fontWeight: '600' },
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 14,
    marginBottom: 20,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 5,
  },
  loginBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  signupRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center' },
  signupLabel: { fontSize: 14 },
  signupLink: { fontWeight: '700', fontSize: 14 },
});
