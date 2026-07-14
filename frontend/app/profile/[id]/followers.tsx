import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useTheme } from '../../../constants/theme';
import { getFollowers } from '../../api/client';
import UserCard from '../../../components/UserCard';
import { Ionicons } from '@expo/vector-icons';

export default function FollowersScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const theme = useTheme();
  const router = useRouter();

  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const fetchFollowers = async () => {
      try {
        const res = await getFollowers(id, 50, 0);
        if (res.data && res.data.items) {
          setUsers(res.data.items);
        }
      } catch (e) {
        console.warn('Failed to fetch followers', e);
      } finally {
        setLoading(false);
      }
    };
    fetchFollowers();
  }, [id]);

  return (
    <View style={[styles.root, { backgroundColor: theme.bg }]}>
      <View style={[styles.header, { backgroundColor: theme.bgCard, borderBottomColor: theme.border }]}>
        <Ionicons name="arrow-back" size={24} color={theme.textPrimary} onPress={() => router.back()} />
        <Text style={[styles.headerTitle, { color: theme.textPrimary }]}>Followers</Text>
        <View style={{ width: 24 }} />
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      ) : (
        <FlatList
          data={users}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <UserCard user={item} />}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.centered}>
              <Text style={{ color: theme.textMuted }}>No followers yet.</Text>
            </View>
          }
        />
      )}
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
  headerTitle: { fontSize: 18, fontWeight: '700' },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', marginTop: 40 },
  listContent: { padding: 16, paddingBottom: 100 },
});
