import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  TextInput,
  Switch,
  Alert,
  StyleSheet,
  Platform,
  ScrollView,
} from 'react-native';
import Animated, {
  FadeInDown,
  FadeInUp,
  ZoomIn,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getCommunities, createCommunity } from '../api/client';
import { useTheme, COMMUNITY_PURPOSE_META } from '../../constants/theme';
import Header from '../../components/Header';

const PURPOSES = ['education', 'fun', 'technology', 'sports', 'gaming', 'business', 'other'];

// ── Community Card ─────────────────────────────────────────────────────────
function CommunityCard({ item, index, theme, router }: any) {
  const meta = COMMUNITY_PURPOSE_META[item.purpose] ?? COMMUNITY_PURPOSE_META['other'];

  const scale = useSharedValue(1);
  const pressStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  return (
    <Animated.View entering={FadeInDown.delay(index * 60).duration(400).springify()}>
      <Animated.View style={pressStyle}>
        <TouchableOpacity
          style={[
            styles.card,
            { backgroundColor: theme.bgCard, borderColor: theme.border },
          ]}
          onPress={() => router.push(`/community/${item.id}`)}
          onPressIn={() => { scale.value = withSpring(0.97, { damping: 10 }); }}
          onPressOut={() => { scale.value = withSpring(1, { damping: 10 }); }}
          activeOpacity={1}
        >
          {/* Accent top stripe */}
          <View style={[styles.cardStripe, { backgroundColor: meta.color }]} />

          <View style={styles.cardBody}>
            {/* Icon + Name Row */}
            <View style={styles.cardHeader}>
              <View style={[styles.purposeIcon, { backgroundColor: meta.color + '20' }]}>
                <Text style={styles.purposeEmoji}>{meta.emoji}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.communityName, { color: theme.textPrimary }]}>
                  c/{item.name}
                </Text>
                <Text style={[styles.uniqueName, { color: theme.textMuted }]}>@{item.unique_name}</Text>
              </View>
              <View
                style={[
                  styles.publicBadge,
                  {
                    backgroundColor: item.is_public
                      ? theme.success + '20'
                      : theme.error + '20',
                    borderColor: item.is_public
                      ? theme.success + '40'
                      : theme.error + '40',
                  },
                ]}
              >
                <Ionicons
                  name={item.is_public ? 'earth-outline' : 'lock-closed-outline'}
                  size={11}
                  color={item.is_public ? theme.success : theme.error}
                />
                <Text
                  style={[
                    styles.publicText,
                    { color: item.is_public ? theme.success : theme.error },
                  ]}
                >
                  {item.is_public ? 'Public' : 'Private'}
                </Text>
              </View>
            </View>

            {/* Description */}
            {item.about ? (
              <Text style={[styles.about, { color: theme.textSecondary }]} numberOfLines={2}>
                {item.about}
              </Text>
            ) : null}

            {/* Purpose tag */}
            <View style={styles.cardFooter}>
              <View style={[styles.purposeTag, { backgroundColor: meta.color + '15', borderColor: meta.color + '40' }]}>
                <Text style={[styles.purposeTagText, { color: meta.color }]}>
                  {meta.emoji} {item.purpose}
                </Text>
              </View>
              <View style={styles.memberCount}>
                <Ionicons name="people-outline" size={13} color={theme.textMuted} />
                <Text style={[styles.memberText, { color: theme.textMuted }]}>
                  {item.members_count ?? '—'} members
                </Text>
              </View>
            </View>
          </View>
        </TouchableOpacity>
      </Animated.View>
    </Animated.View>
  );
}

export default function CommunitiesScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [communities, setCommunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  const [name, setName] = useState('');
  const [about, setAbout] = useState('');
  const [purpose, setPurpose] = useState('other');
  const [isPublic, setIsPublic] = useState(true);
  const [creating, setCreating] = useState(false);

  // FAB animation
  const fabScale = useSharedValue(1);
  const fabStyle = useAnimatedStyle(() => ({ transform: [{ scale: fabScale.value }] }));

  const fetchCommunities = async () => {
    try {
      const res = await getCommunities(1, 50);
      if (res.success) setCommunities(res.data.items || res.data || []);
    } catch {
      console.warn('Failed to fetch communities');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchCommunities(); }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchCommunities();
  };

  const handleCreate = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Community name is required');
      return;
    }
    setCreating(true);
    try {
      const res = await createCommunity({ name, about: about || undefined, purpose, is_public: isPublic });
      if (res.success) {
        setModalVisible(false);
        setName(''); setAbout(''); setPurpose('other'); setIsPublic(true);
        handleRefresh();
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to create community');
    } finally {
      setCreating(false);
    }
  };

  return (
    <View style={[styles.root, { backgroundColor: theme.bg }]}>
      <Header title="Communities" />

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      ) : (
        <FlatList
          data={communities}
          keyExtractor={(item) => item.id}
          renderItem={({ item, index }) => (
            <CommunityCard item={item} index={index} theme={theme} router={router} />
          )}
          contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
          refreshing={refreshing}
          onRefresh={handleRefresh}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <Animated.View entering={FadeInDown.delay(200).duration(600)} style={styles.empty}>
              <View style={[styles.emptyIcon, { backgroundColor: theme.bgSubtle }]}>
                <Ionicons name="people-outline" size={48} color={theme.textMuted} />
              </View>
              <Text style={[styles.emptyTitle, { color: theme.textPrimary }]}>No communities yet</Text>
              <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
                Create the first one!
              </Text>
            </Animated.View>
          }
        />
      )}

      {/* FAB */}
      <Animated.View style={[styles.fab, { backgroundColor: theme.accent }, fabStyle]}>
        <TouchableOpacity
          onPress={() => {
            fabScale.value = withSequence(
              withSpring(0.85, { damping: 8 }),
              withSpring(1, { damping: 10 })
            );
            setModalVisible(true);
          }}
          style={styles.fabInner}
          activeOpacity={1}
        >
          <Ionicons name="add" size={30} color="#fff" />
        </TouchableOpacity>
      </Animated.View>

      {/* Create Modal */}
      <Modal
        animationType="slide"
        transparent
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={[styles.modalOverlay, { backgroundColor: theme.overlay }]}>
          <Animated.View
            entering={FadeInUp.duration(350).springify()}
            style={[styles.modalSheet, { backgroundColor: theme.bgCard }]}
          >
            {/* Modal handle */}
            <View style={[styles.modalHandle, { backgroundColor: theme.border }]} />

            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.textPrimary }]}>
                Create Community
              </Text>
              <TouchableOpacity
                onPress={() => setModalVisible(false)}
                style={[styles.modalClose, { backgroundColor: theme.bgSubtle }]}
              >
                <Ionicons name="close" size={20} color={theme.textSecondary} />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              {/* Name */}
              <View style={styles.formGroup}>
                <Text style={[styles.formLabel, { color: theme.textSecondary }]}>Name *</Text>
                <TextInput
                  style={[styles.formInput, { backgroundColor: theme.bgSubtle, borderColor: theme.border, color: theme.textPrimary }]}
                  placeholder="e.g. Delhi Drivers Hub"
                  placeholderTextColor={theme.textMuted}
                  value={name}
                  onChangeText={setName}
                />
              </View>

              {/* About */}
              <View style={styles.formGroup}>
                <Text style={[styles.formLabel, { color: theme.textSecondary }]}>About (optional)</Text>
                <TextInput
                  style={[styles.formInput, styles.formTextArea, { backgroundColor: theme.bgSubtle, borderColor: theme.border, color: theme.textPrimary }]}
                  placeholder="What is this community about?"
                  placeholderTextColor={theme.textMuted}
                  value={about}
                  onChangeText={setAbout}
                  multiline
                  textAlignVertical="top"
                />
              </View>

              {/* Purpose chips */}
              <View style={styles.formGroup}>
                <Text style={[styles.formLabel, { color: theme.textSecondary }]}>Purpose</Text>
                <View style={styles.purposeChips}>
                  {PURPOSES.map((p) => {
                    const meta = COMMUNITY_PURPOSE_META[p];
                    const isSelected = purpose === p;
                    return (
                      <TouchableOpacity
                        key={p}
                        onPress={() => setPurpose(p)}
                        style={[
                          styles.purposeChip,
                          {
                            backgroundColor: isSelected ? theme.accent : theme.bgSubtle,
                            borderColor: isSelected ? theme.accent : theme.border,
                          },
                        ]}
                      >
                        <Text style={styles.chipEmoji}>{meta.emoji}</Text>
                        <Text
                          style={[
                            styles.chipText,
                            { color: isSelected ? '#fff' : theme.textSecondary },
                          ]}
                        >
                          {p}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>

              {/* Public toggle */}
              <View style={[styles.toggleRow, { backgroundColor: theme.bgSubtle, borderColor: theme.border }]}>
                <View>
                  <Text style={[styles.toggleLabel, { color: theme.textPrimary }]}>Public Community</Text>
                  <Text style={[styles.toggleSub, { color: theme.textMuted }]}>Anyone can join</Text>
                </View>
                <Switch
                  value={isPublic}
                  onValueChange={setIsPublic}
                  trackColor={{ false: theme.bgMuted, true: theme.accent }}
                  thumbColor="#fff"
                />
              </View>

              {/* Submit */}
              <TouchableOpacity
                style={[
                  styles.submitBtn,
                  { backgroundColor: name.trim() ? theme.accent : theme.textMuted },
                ]}
                onPress={handleCreate}
                disabled={creating || !name.trim()}
                activeOpacity={0.85}
              >
                {creating ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.submitText}>Create Community</Text>
                )}
              </TouchableOpacity>
            </ScrollView>
          </Animated.View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 56 : 40,
    paddingBottom: 14,
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: 24, fontWeight: '800', letterSpacing: -0.5 },
  headerRight: { flexDirection: 'row', gap: 10 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  card: {
    borderRadius: 18,
    marginBottom: 12,
    borderWidth: 1,
    overflow: 'hidden',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },
  cardStripe: { height: 4, width: '100%' },
  cardBody: { padding: 14, gap: 10 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  purposeIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  purposeEmoji: { fontSize: 22 },
  communityName: { fontSize: 15, fontWeight: '700' },
  uniqueName: { fontSize: 12, marginTop: 1 },
  publicBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
  },
  publicText: { fontSize: 10, fontWeight: '700' },
  about: { fontSize: 13, lineHeight: 18 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  purposeTag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  purposeTagText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  memberCount: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  memberText: { fontSize: 11 },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 20,
    width: 58,
    height: 58,
    borderRadius: 29,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 8,
  },
  fabInner: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80, gap: 12 },
  emptyIcon: { width: 88, height: 88, borderRadius: 44, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  emptyTitle: { fontSize: 20, fontWeight: '700' },
  emptySubtitle: { fontSize: 14, textAlign: 'center' },
  // Modal
  modalOverlay: { flex: 1, justifyContent: 'flex-end' },
  modalSheet: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 20,
    paddingBottom: Platform.OS === 'ios' ? 40 : 24,
    maxHeight: '90%',
  },
  modalHandle: { width: 40, height: 4, borderRadius: 2, alignSelf: 'center', marginBottom: 16 },
  modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  modalTitle: { fontSize: 20, fontWeight: '800' },
  modalClose: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  formGroup: { marginBottom: 16 },
  formLabel: { fontSize: 13, fontWeight: '600', marginBottom: 6, marginLeft: 2 },
  formInput: { borderWidth: 1.5, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15 },
  formTextArea: { height: 88, textAlignVertical: 'top' },
  purposeChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  purposeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
  },
  chipEmoji: { fontSize: 14 },
  chipText: { fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 20,
  },
  toggleLabel: { fontSize: 15, fontWeight: '600' },
  toggleSub: { fontSize: 12, marginTop: 2 },
  submitBtn: { paddingVertical: 16, borderRadius: 14, alignItems: 'center' },
  submitText: { color: '#fff', fontWeight: '700', fontSize: 16 },
});
