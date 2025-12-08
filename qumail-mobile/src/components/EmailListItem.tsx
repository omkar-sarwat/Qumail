import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Animated, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Swipeable } from 'react-native-gesture-handler';
import { Email } from '../types';
import { colors, spacing, borderRadius, typography, shadows } from '../constants/theme';

interface EmailListItemProps {
  email: Email;
  onPress: () => void;
  onStarPress: () => void;
  onDelete?: () => void;
  onArchive?: () => void;
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
};

const getAvatarColor = (name: string) => {
  const colorsList = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colorsList[Math.abs(hash) % colorsList.length];
};

export const EmailListItem: React.FC<EmailListItemProps> = ({
  email,
  onPress,
  onStarPress,
  onDelete,
  onArchive,
}) => {
  const renderRightActions = (progress: Animated.AnimatedInterpolation<number>, dragX: Animated.AnimatedInterpolation<number>) => {
    const scale = dragX.interpolate({
      inputRange: [-100, 0],
      outputRange: [1, 0],
      extrapolate: 'clamp',
    });

    return (
      <TouchableOpacity onPress={onArchive} style={styles.rightAction}>
        <Animated.View style={[styles.actionIcon, { transform: [{ scale }] }]}>
          <Ionicons name="archive-outline" size={24} color="white" />
        </Animated.View>
      </TouchableOpacity>
    );
  };

  const renderLeftActions = (progress: Animated.AnimatedInterpolation<number>, dragX: Animated.AnimatedInterpolation<number>) => {
    const scale = dragX.interpolate({
      inputRange: [0, 100],
      outputRange: [0, 1],
      extrapolate: 'clamp',
    });

    return (
      <TouchableOpacity onPress={onDelete} style={styles.leftAction}>
        <Animated.View style={[styles.actionIcon, { transform: [{ scale }] }]}>
          <Ionicons name="trash-outline" size={24} color="white" />
        </Animated.View>
      </TouchableOpacity>
    );
  };

  // Determine avatar source - use image for specific names to match design
  const getAvatarSource = () => {
    if (email.from.name.includes('Priya')) {
      return { uri: 'https://i.pravatar.cc/150?img=5' };
    } else if (email.from.name.includes('Neha')) {
      return { uri: 'https://i.pravatar.cc/150?img=9' };
    } else if (email.from.name.includes('Kavitha')) {
      return { uri: 'https://i.pravatar.cc/150?img=25' };
    }
    return null;
  };

  // Get encryption level label
  const getEncryptionLabel = () => {
    if (!email.encryptionLevel) return null;
    const labels: { [key: number]: { label: string; color: keyof typeof colors.tags } } = {
      1: { label: 'Level 1 - OTP', color: 'green' },
      2: { label: 'Level 2 - AES', color: 'blue' },
      3: { label: 'Level 3 - PQC', color: 'purple' },
      4: { label: 'Level 4 - RSA', color: 'orange' },
    };
    return labels[email.encryptionLevel];
  };

  const encryptionLabel = getEncryptionLabel();
  const avatarSource = getAvatarSource();

  return (
    <View style={styles.wrapper}>
      <Swipeable
        renderRightActions={renderRightActions}
        renderLeftActions={renderLeftActions}
        containerStyle={styles.swipeableContainer}
      >
        <TouchableOpacity 
          style={[
            styles.container, 
            !email.isRead && styles.unreadContainer
          ]} 
          onPress={onPress}
          activeOpacity={0.9}
        >
          {/* Avatar Section */}
          <View style={styles.avatarContainer}>
            {avatarSource ? (
              <Image source={avatarSource} style={styles.avatarImage} />
            ) : (
              <View style={[styles.avatar, { backgroundColor: getAvatarColor(email.from.name) }]}>
                {email.from.name.includes('Oriental') ? (
                  <Ionicons name="business" size={20} color="white" />
                ) : (
                  <Text style={styles.avatarText}>{email.from.name.charAt(0).toUpperCase()}</Text>
                )}
              </View>
            )}
            
            {/* Encryption Badge on Avatar */}
            {email.encryptionLevel && email.encryptionLevel > 0 && (
              <View style={[styles.securityBadge, { backgroundColor: colors.encryption[`level${email.encryptionLevel}` as keyof typeof colors.encryption] }]} />
            )}
          </View>

          {/* Content Section */}
          <View style={styles.content}>
            <View style={styles.headerRow}>
              <View style={styles.senderRow}>
                {/* Reply Icon if it's a reply */}
                {email.subject.startsWith('RE:') && (
                  <Ionicons name="arrow-undo" size={12} color={colors.textMuted} style={{ marginRight: 4 }} />
                )}
                <Text style={[styles.sender, !email.isRead && styles.unreadText]} numberOfLines={1}>
                  {email.from.name}
                </Text>
              </View>
              <Text style={styles.time}>{formatDate(email.date)}</Text>
            </View>
            
            <Text style={[styles.subject, !email.isRead && styles.unreadText]} numberOfLines={1}>
              {email.subject}
            </Text>
            
            {/* Tags Row */}
            {email.tags && email.tags.length > 0 && (
              <View style={styles.tagsRow}>
                {email.tags.map((tag, index) => (
                  <View 
                    key={index} 
                    style={[
                      styles.tag, 
                      { backgroundColor: colors.tags[tag.color]?.bg || colors.tags.blue.bg }
                    ]}
                  >
                    <Text 
                      style={[
                        styles.tagText, 
                        { color: colors.tags[tag.color]?.text || colors.tags.blue.text }
                      ]}
                    >
                      {tag.label}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </View>

          {/* Right Actions (Star) */}
          <View style={styles.rightActions}>
             <TouchableOpacity onPress={onStarPress} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Ionicons 
                  name={email.isStarred ? "star" : "star-outline"} 
                  size={18} 
                  color={email.isStarred ? colors.secondary : colors.textMuted} 
                />
              </TouchableOpacity>
              {email.hasAttachments && (
                 <Ionicons name="attach" size={16} color={colors.textMuted} style={{ marginTop: 8 }} />
              )}
          </View>
        </TouchableOpacity>
      </Swipeable>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: 1, // Minimal spacing for divider look without actual divider
    backgroundColor: colors.surface,
  },
  swipeableContainer: {
    backgroundColor: colors.surface,
  },
  container: {
    flexDirection: 'row',
    padding: spacing.md,
    backgroundColor: colors.surface,
    alignItems: 'flex-start', // Align top for multi-line content
  },
  unreadContainer: {
    backgroundColor: colors.surface,
  },
  avatarContainer: {
    marginRight: spacing.md,
    position: 'relative',
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 16, // Squircle shape
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarImage: {
    width: 48,
    height: 48,
    borderRadius: 16,
  },
  avatarText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  securityBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: colors.surface,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  senderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sender: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginRight: spacing.sm,
  },
  time: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '500',
  },
  subject: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: 8,
    fontWeight: '400',
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tagText: {
    fontSize: 11,
    fontWeight: '600',
  },
  unreadText: {
    color: colors.textPrimary,
    fontWeight: '700',
  },
  rightActions: {
    alignItems: 'center',
    marginLeft: spacing.sm,
    paddingTop: 2,
  },
  leftAction: {
    backgroundColor: colors.accent,
    justifyContent: 'center',
    alignItems: 'flex-start',
    paddingLeft: 20,
    flex: 1,
  },
  rightAction: {
    backgroundColor: colors.encryption.level1, // Green for archive
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingRight: 20,
    flex: 1,
  },
  actionIcon: {
    width: 30,
    alignItems: 'center',
  },
});
