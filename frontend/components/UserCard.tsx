import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme } from '../constants/theme';
import { followUser, unfollowUser } from '../app/api/client';
import apiClient from '../app/api/client';

export interface UserCardProps {
  user: any;
  onFollowChange?: (userId: string, isFollowing: boolean) => void;
}

export default function UserCard({ user, onFollowChange }: UserCardProps) {
  const theme = useTheme();
  const router = useRouter();
  
  const [isFollowing, setIsFollowing] = useState(user.is_following);
  const [isMutual, setIsMutual] = useState(user.is_mutual);
  const [loading, setLoading] = useState(false);

  const handleFollowToggle = async () => {
    setLoading(true);
    try {
      if (isFollowing) {
        await unfollowUser(user.id);
        setIsFollowing(false);
        setIsMutual(false);
        if (onFollowChange) onFollowChange(user.id, false);
      } else {
        await followUser(user.id);
        setIsFollowing(true);
        // Optimistically check mutual if they follow us
        if (user.is_followed_by) {
          setIsMutual(true);
        }
        if (onFollowChange) onFollowChange(user.id, true);
      }
    } catch (e: any) {
      Alert.alert("Error", e.response?.data?.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleMessage = async () => {
    try {
      const res = await apiClient.post('/chat/conversations/direct', { target_user_id: user.id });
      if (res.data) {
        router.push(`/chats/${res.data.id}`);
      }
    } catch (e: any) {
      Alert.alert("Notice", e.response?.data?.detail || "You can only chat if you mutually follow each other.");
    }
  };

  return (
    <View style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
      <View style={styles.left}>
        {user.avatar ? (
          <Image source={{ uri: user.avatar }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatarPlaceholder, { backgroundColor: theme.bgSubtle }]}>
            <Ionicons name="person" size={24} color={theme.textMuted} />
          </View>
        )}
        <View style={styles.info}>
          <Text style={[styles.name, { color: theme.textPrimary }]} numberOfLines={1}>
            {user.full_name}
          </Text>
          <Text style={[styles.username, { color: theme.textMuted }]} numberOfLines={1}>
            {user.username ? `@${user.username}` : user.email}
          </Text>
          {isMutual && (
            <View style={[styles.mutualBadge, { backgroundColor: theme.accent + '20' }]}>
              <Ionicons name="swap-horizontal" size={12} color={theme.accent} />
              <Text style={[styles.mutualText, { color: theme.accent }]}>Mutual Follow</Text>
            </View>
          )}
        </View>
      </View>
      
      <View style={styles.actions}>
        {isMutual && (
          <TouchableOpacity onPress={handleMessage} style={[styles.iconButton, { backgroundColor: theme.bgSubtle }]}>
            <Ionicons name="chatbubble-ellipses-outline" size={20} color={theme.accent} />
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[
            styles.followButton,
            { 
              backgroundColor: isFollowing ? theme.bgSubtle : theme.accent,
              borderColor: isFollowing ? theme.border : theme.accent
            }
          ]}
          onPress={handleFollowToggle}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color={isFollowing ? theme.textPrimary : '#fff'} />
          ) : (
            <Text style={[styles.followButtonText, { color: isFollowing ? theme.textPrimary : '#fff' }]}>
              {isFollowing ? 'Following' : 'Follow'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 10,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  avatarPlaceholder: {
    width: 50,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
  },
  info: {
    marginLeft: 12,
    flex: 1,
    justifyContent: 'center',
  },
  name: {
    fontSize: 16,
    fontWeight: '700',
  },
  username: {
    fontSize: 13,
    marginTop: 2,
  },
  mutualBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 4,
    gap: 4,
  },
  mutualText: {
    fontSize: 10,
    fontWeight: '600',
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  iconButton: {
    padding: 8,
    borderRadius: 12,
  },
  followButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    minWidth: 90,
    alignItems: 'center',
  },
  followButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
});
