import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Image,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Dimensions,
} from 'react-native';
import Animated, {
  FadeInDown,
  FadeInUp,
  ZoomIn,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  interpolateColor,
} from 'react-native-reanimated';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { getProfile, updateProfile } from '../api/client';
import { useAuthStore } from '../../store/authStore';
import { useTheme } from '../../constants/theme';
import Header from '../../components/Header';

const { width } = Dimensions.get('window');

// ── Profile Stat Tile ──────────────────────────────────────────────────────
function StatTile({ label, value, icon, theme }: any) {
  return (
    <Animated.View
      entering={ZoomIn.delay(300).duration(400)}
      style={[styles.statTile, { backgroundColor: theme.bgCard, borderColor: theme.border }]}
    >
      <Ionicons name={icon} size={20} color={theme.accent} />
      <Text style={[styles.statValue, { color: theme.textPrimary }]}>{value}</Text>
      <Text style={[styles.statLabel, { color: theme.textMuted }]}>{label}</Text>
    </Animated.View>
  );
}

// ── Animated Text Field ────────────────────────────────────────────────────
function ProfileField({ label, value, onChangeText, multiline, keyboardType, theme }: any) {
  const focus = useSharedValue(0);
  const containerStyle = useAnimatedStyle(() => ({
    borderColor: interpolateColor(focus.value, [0, 1], [theme.border, theme.accent]),
  }));

  return (
    <View style={styles.fieldGroup}>
      <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>{label}</Text>
      <Animated.View
        style={[
          styles.fieldInput,
          { backgroundColor: theme.bgSubtle },
          containerStyle,
        ]}
      >
        <TextInput
          style={[
            styles.fieldTextInput,
            { color: theme.textPrimary },
            multiline && { minHeight: 80, textAlignVertical: 'top' },
          ]}
          value={value}
          onChangeText={onChangeText}
          placeholder={label}
          placeholderTextColor={theme.textMuted}
          multiline={multiline}
          keyboardType={keyboardType}
          onFocus={() => { focus.value = withTiming(1, { duration: 200 }); }}
          onBlur={() => { focus.value = withTiming(0, { duration: 200 }); }}
        />
      </Animated.View>
    </View>
  );
}

export default function ProfileScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { logout, user: authUser, setUser } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState<any>(null);

  const [formData, setFormData] = useState({
    full_name: '',
    bio: '',
    company: '',
    vehicle_type: '',
    phone_number: '',
  });

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await getProfile();
      if (response.success) {
        setProfile(response.data);
        setFormData({
          full_name: response.data.full_name || '',
          bio: response.data.bio || '',
          company: response.data.company || '',
          vehicle_type: response.data.vehicle_type || '',
          phone_number: response.data.phone_number || '',
        });
      }
    } catch {
      Alert.alert('Error', 'Failed to load profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProfile(); }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await updateProfile(formData);
      if (response.success) {
        setProfile(response.data);
        if (authUser) setUser({ ...authUser, ...response.data });
        setIsEditing(false);
        Alert.alert('Success', 'Profile updated!');
      }
    } catch {
      Alert.alert('Error', 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  if (loading) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.bg }]}>
        <ActivityIndicator size="large" color={theme.accent} />
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.bg }]}>
        <Text style={{ color: theme.textMuted }}>Could not load profile.</Text>
      </View>
    );
  }

  const authorInitial = (profile.full_name || 'U').charAt(0).toUpperCase();

  return (
    <KeyboardAvoidingView
      style={[styles.root, { backgroundColor: theme.bg }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Header title="Profile" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 40 }}
      >
        {/* Hero Banner */}
        <Animated.View
          entering={FadeInDown.duration(500)}
          style={[styles.heroBanner, { backgroundColor: theme.accent + '22' }]}
        >

          {/* Avatar */}
          <View style={styles.avatarWrapper}>
            {profile.avatar ? (
              <Image source={{ uri: profile.avatar }} style={styles.avatar} />
            ) : (
              <View style={[styles.avatarPlaceholder, { backgroundColor: theme.accent }]}>
                <Text style={styles.avatarInitial}>{authorInitial}</Text>
              </View>
            )}
            {profile.is_verified && (
              <Animated.View
                entering={ZoomIn.delay(400)}
                style={[styles.verifiedBadge, { backgroundColor: theme.success }]}
              >
                <Ionicons name="checkmark" size={12} color="#fff" />
              </Animated.View>
            )}
          </View>

          {/* Name & email */}
          <Animated.Text
            entering={FadeInUp.delay(200).duration(500)}
            style={[styles.name, { color: theme.textPrimary }]}
          >
            {profile.full_name}
          </Animated.Text>
          <Animated.Text
            entering={FadeInUp.delay(300).duration(500)}
            style={[styles.email, { color: theme.textSecondary }]}
          >
            {profile.email}
          </Animated.Text>

          {/* Followers / Following Links */}
          <Animated.View entering={FadeInUp.delay(400).duration(500)} style={styles.followRow}>
            <TouchableOpacity onPress={() => router.push(`/profile/${profile.id}/followers`)}>
              <Text style={[styles.followText, { color: theme.textPrimary }]}>
                <Text style={{ fontWeight: 'bold' }}>{profile.follower_count}</Text> Followers
              </Text>
            </TouchableOpacity>
            <View style={[styles.followDivider, { backgroundColor: theme.textMuted }]} />
            <TouchableOpacity onPress={() => router.push(`/profile/${profile.id}/following`)}>
              <Text style={[styles.followText, { color: theme.textPrimary }]}>
                <Text style={{ fontWeight: 'bold' }}>{profile.following_count}</Text> Following
              </Text>
            </TouchableOpacity>
          </Animated.View>
        </Animated.View>

        {/* Stats Row */}
        <View style={styles.statsRow}>
          <StatTile label="Verified" value={profile.is_verified ? 'Yes' : 'No'} icon="shield-checkmark-outline" theme={theme} />
          <StatTile label="Vehicle" value={profile.vehicle_type || '—'} icon="bicycle-outline" theme={theme} />
          <StatTile label="Company" value={profile.company ? profile.company.split(' ')[0] : '—'} icon="briefcase-outline" theme={theme} />
        </View>

        {/* Content */}
        <View style={styles.content}>
          {isEditing ? (
            /* Edit Mode */
            <Animated.View entering={FadeInDown.duration(400)} style={styles.editCard}>
              <View style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
                <Text style={[styles.sectionTitle, { color: theme.textPrimary }]}>Edit Profile</Text>

                <ProfileField label="Full Name" value={formData.full_name} onChangeText={(t: string) => setFormData(p => ({ ...p, full_name: t }))} theme={theme} />
                <ProfileField label="Bio" value={formData.bio} onChangeText={(t: string) => setFormData(p => ({ ...p, bio: t }))} multiline theme={theme} />
                <ProfileField label="Company" value={formData.company} onChangeText={(t: string) => setFormData(p => ({ ...p, company: t }))} theme={theme} />
                <ProfileField label="Vehicle Type" value={formData.vehicle_type} onChangeText={(t: string) => setFormData(p => ({ ...p, vehicle_type: t }))} theme={theme} />
                <ProfileField label="Phone Number" value={formData.phone_number} onChangeText={(t: string) => setFormData(p => ({ ...p, phone_number: t }))} keyboardType="phone-pad" theme={theme} />

                <View style={styles.editBtns}>
                  <TouchableOpacity
                    style={[styles.cancelBtn, { backgroundColor: theme.bgSubtle, borderColor: theme.border }]}
                    onPress={() => setIsEditing(false)}
                    disabled={saving}
                  >
                    <Text style={[styles.cancelBtnText, { color: theme.textSecondary }]}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.saveBtn, { backgroundColor: theme.accent }]}
                    onPress={handleSave}
                    disabled={saving}
                  >
                    {saving ? <ActivityIndicator color="#fff" size="small" /> : (
                      <Text style={styles.saveBtnText}>Save Changes</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </Animated.View>
          ) : (
            /* View Mode */
            <Animated.View entering={FadeInDown.delay(100).duration(500)}>
              {/* Info Card */}
              <View style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
                <Text style={[styles.sectionTitle, { color: theme.textPrimary }]}>About</Text>
                <Text style={[styles.bioText, { color: theme.textSecondary }]}>
                  {profile.bio || 'No bio added yet.'}
                </Text>

                <View style={[styles.separator, { backgroundColor: theme.border }]} />

                {[
                  { icon: 'briefcase-outline', text: profile.company || 'No company' },
                  { icon: 'bicycle-outline', text: profile.vehicle_type || 'No vehicle' },
                  { icon: 'call-outline', text: profile.phone_number || 'No phone' },
                ].map((row, i) => (
                  <View key={i} style={styles.infoRow}>
                    <Ionicons name={row.icon as any} size={18} color={theme.accent} />
                    <Text style={[styles.infoText, { color: theme.textSecondary }]}>{row.text}</Text>
                  </View>
                ))}
              </View>

              {/* Action buttons */}
              <View style={styles.actionBtns}>
                <TouchableOpacity
                  style={[styles.actionBtn, { backgroundColor: theme.bgCard, borderColor: theme.border }]}
                  onPress={() => router.push('/bookmarks')}
                >
                  <Ionicons name="bookmark-outline" size={20} color={theme.accent} />
                  <Text style={[styles.actionBtnText, { color: theme.textPrimary }]}>Saved Bookmarks</Text>
                  <Ionicons name="chevron-forward" size={16} color={theme.textMuted} style={{ marginLeft: 'auto' }} />
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionBtn, { backgroundColor: theme.accentLight, borderColor: theme.accent + '40' }]}
                  onPress={() => setIsEditing(true)}
                >
                  <Feather name="edit-3" size={18} color={theme.accent} />
                  <Text style={[styles.actionBtnText, { color: theme.accent }]}>Edit Profile</Text>
                  <Ionicons name="chevron-forward" size={16} color={theme.accent} style={{ marginLeft: 'auto' }} />
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionBtn, styles.logoutBtn]}
                  onPress={handleLogout}
                >
                  <Ionicons name="log-out-outline" size={20} color="#EF4444" />
                  <Text style={[styles.actionBtnText, { color: '#EF4444' }]}>Logout</Text>
                </TouchableOpacity>
              </View>
            </Animated.View>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  heroBanner: {
    alignItems: 'center',
    paddingBottom: 24,
    paddingTop: 32,
  },
  heroTopBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  heroTitle: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5 },
  avatarWrapper: { position: 'relative', marginBottom: 12 },
  avatar: { width: 88, height: 88, borderRadius: 44 },
  avatarPlaceholder: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: { color: '#fff', fontWeight: '800', fontSize: 36 },
  verifiedBadge: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  name: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5, marginBottom: 4 },
  email: { fontSize: 14 },
  followRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  followText: {
    fontSize: 14,
  },
  followDivider: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginHorizontal: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    marginTop: -10,
    marginBottom: 4,
  },
  statTile: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1,
    gap: 4,
  },
  statValue: { fontWeight: '700', fontSize: 13 },
  statLabel: { fontSize: 10, textAlign: 'center' },
  content: { padding: 16, gap: 12 },
  card: {
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    gap: 12,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  editCard: { gap: 0 },
  sectionTitle: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  bioText: { fontSize: 14, lineHeight: 20 },
  separator: { height: 1, marginVertical: 4 },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 6 },
  infoText: { fontSize: 14 },
  fieldGroup: { gap: 6 },
  fieldLabel: { fontSize: 12, fontWeight: '600', marginLeft: 4 },
  fieldInput: {
    borderWidth: 1.5,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  fieldTextInput: { fontSize: 15 },
  editBtns: { flexDirection: 'row', gap: 10, marginTop: 8 },
  cancelBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
  },
  cancelBtnText: { fontWeight: '600', fontSize: 15 },
  saveBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 12,
  },
  saveBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  actionBtns: { gap: 10 },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
  },
  actionBtnText: { fontWeight: '600', fontSize: 15 },
  logoutBtn: { backgroundColor: '#FEE2E2', borderColor: '#FECACA' },
});
