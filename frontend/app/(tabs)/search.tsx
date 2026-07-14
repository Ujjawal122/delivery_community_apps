import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, TextInput, FlatList, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import { useTheme } from '../../constants/theme';
import { searchUsers, getSuggestions } from '../api/client';
import UserCard from '../../components/UserCard';
import { Ionicons } from '@expo/vector-icons';
import Animated, { FadeInDown } from 'react-native-reanimated';

export default function SearchScreen() {
  const theme = useTheme();
  
  const [query, setQuery] = useState('');
  const [users, setUsers] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);

  // Fetch suggestions on mount
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const res = await getSuggestions(10);
        if (res.data && res.data.items) {
          setSuggestions(res.data.items);
        }
      } catch (e) {
        console.warn("Error fetching suggestions", e);
      } finally {
        setLoading(false);
      }
    };
    fetchInitial();
  }, []);

  // Debounced Search
  useEffect(() => {
    if (!query.trim()) {
      setUsers([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await searchUsers(query, 20, 0);
        if (res.data && res.data.items) {
          setUsers(res.data.items);
        }
      } catch (e) {
        console.warn("Search error", e);
      } finally {
        setSearching(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const renderEmpty = () => {
    if (loading || searching) return null;
    
    if (query.trim() && users.length === 0) {
      return (
        <View style={styles.emptyContainer}>
          <Ionicons name="search-outline" size={48} color={theme.textMuted} />
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No users found for "{query}"</Text>
        </View>
      );
    }

    if (!query.trim() && suggestions.length > 0) {
      return (
        <View style={styles.suggestionsContainer}>
          <Text style={[styles.sectionTitle, { color: theme.textPrimary }]}>Suggested for you</Text>
          {suggestions.map((user, index) => (
            <Animated.View key={user.id} entering={FadeInDown.delay(index * 50)}>
              <UserCard user={user} />
            </Animated.View>
          ))}
        </View>
      );
    }

    return null;
  };

  return (
    <View style={[styles.root, { backgroundColor: theme.bg }]}>
      <View style={[styles.header, { backgroundColor: theme.bgCard, borderBottomColor: theme.border }]}>
        <Text style={[styles.headerTitle, { color: theme.textPrimary }]}>Search</Text>
        <View style={[styles.searchBar, { backgroundColor: theme.bgSubtle, borderColor: theme.border }]}>
          <Ionicons name="search" size={20} color={theme.textMuted} />
          <TextInput
            style={[styles.searchInput, { color: theme.textPrimary }]}
            placeholder="Search by name or email..."
            placeholderTextColor={theme.textMuted}
            value={query}
            onChangeText={setQuery}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {query.length > 0 && (
            <Ionicons
              name="close-circle"
              size={20}
              color={theme.textMuted}
              onPress={() => setQuery('')}
            />
          )}
        </View>
      </View>

      <FlatList
        data={query.trim() ? users : []}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <UserCard user={item} />}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={renderEmpty()}
        ListHeaderComponent={
          searching ? <ActivityIndicator style={{ marginVertical: 20 }} color={theme.accent} /> : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 56 : 40,
    paddingBottom: 14,
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: 24, fontWeight: '800', letterSpacing: -0.5, marginBottom: 12 },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
  },
  listContent: {
    padding: 16,
    paddingBottom: 100,
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 60,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
  },
  suggestionsContainer: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
  },
});
