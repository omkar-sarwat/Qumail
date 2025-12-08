import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  StatusBar,
  Image,
  Animated,
  Modal,
  Dimensions,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, borderRadius, typography, shadows } from '../constants/theme';
import { useEmailStore } from '../stores/emailStore';
import { useAuthStore } from '../stores/authStore';
import { Email } from '../types';
import type { RootStackParamList } from '../navigation/AppNavigator';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

// Format date helper
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

// Get avatar color based on name
const getAvatarColor = (name: string) => {
  const colorsList = ['#EA4335', '#FBBC04', '#34A853', '#4285F4', '#9C27B0', '#FF5722', '#00BCD4', '#3F51B5'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colorsList[Math.abs(hash) % colorsList.length];
};

// Get encryption level info
const getEncryptionInfo = (level?: 1 | 2 | 3 | 4) => {
  if (!level) return null;
  const info = {
    1: { label: 'OTP', color: '#34A853', icon: 'shield-checkmark' },
    2: { label: 'AES', color: '#4285F4', icon: 'lock-closed' },
    3: { label: 'PQC', color: '#9C27B0', icon: 'key' },
    4: { label: 'RSA', color: '#FF5722', icon: 'shield' },
  };
  return info[level];
};

// Email Item Component
const EmailItem: React.FC<{
  email: Email;
  onPress: () => void;
  onStarPress: () => void;
}> = ({ email, onPress, onStarPress }) => {
  const encryptionInfo = getEncryptionInfo(email.encryptionLevel);
  
  return (
    <TouchableOpacity style={styles.emailItem} onPress={onPress} activeOpacity={0.7}>
      {/* Avatar */}
      <View style={[styles.avatar, { backgroundColor: getAvatarColor(email.from.name) }]}>
        <Text style={styles.avatarText}>{email.from.name.charAt(0).toUpperCase()}</Text>
        {encryptionInfo && (
          <View style={[styles.encryptionBadge, { backgroundColor: encryptionInfo.color }]}>
            <Ionicons name={encryptionInfo.icon as any} size={8} color="white" />
          </View>
        )}
      </View>

      {/* Email Content */}
      <View style={styles.emailContent}>
        <View style={styles.emailHeader}>
          <Text style={[styles.senderName, !email.isRead && styles.unreadText]} numberOfLines={1}>
            {email.from.name}
          </Text>
          <Text style={styles.emailDate}>{formatDate(email.date)}</Text>
        </View>
        <Text style={[styles.emailSubject, !email.isRead && styles.unreadText]} numberOfLines={1}>
          {email.subject}
        </Text>
        <View style={styles.snippetRow}>
          <Text style={styles.emailSnippet} numberOfLines={1}>
            {email.snippet}
          </Text>
          {encryptionInfo && (
            <View style={[styles.levelTag, { backgroundColor: encryptionInfo.color + '20' }]}>
              <Text style={[styles.levelTagText, { color: encryptionInfo.color }]}>
                L{email.encryptionLevel}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Star Button */}
      <TouchableOpacity onPress={onStarPress} style={styles.starButton}>
        <Ionicons
          name={email.isStarred ? 'star' : 'star-outline'}
          size={20}
          color={email.isStarred ? '#FBBC04' : '#9AA0A6'}
        />
      </TouchableOpacity>
    </TouchableOpacity>
  );
};

// Main Inbox Screen
export const InboxScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const { emails, toggleStar, setCurrentMailbox, currentMailbox, isLoading, refreshEmails, error } = useEmailStore();
  const { user, logout } = useAuthStore();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [showDrawer, setShowDrawer] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const drawerAnim = useState(new Animated.Value(-SCREEN_WIDTH * 0.70))[0];

  // Pull to refresh
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refreshEmails();
    setRefreshing(false);
  }, [refreshEmails]);

  // Filter emails based on search
  const filteredEmails = emails.filter(
    (email: Email) =>
      email.from.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.snippet.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Toggle drawer
  const toggleDrawer = useCallback(() => {
    const toValue = showDrawer ? -SCREEN_WIDTH * 0.70 : 0;
    Animated.spring(drawerAnim, {
      toValue,
      useNativeDriver: true,
      friction: 8,
    }).start();
    setShowDrawer(!showDrawer);
  }, [showDrawer, drawerAnim]);

  // Handle email press
  const handleEmailPress = (emailId: string) => {
    navigation.navigate('EmailDetail', { emailId });
  };

  // Handle compose
  const handleCompose = () => {
    navigation.navigate('Compose');
  };

  // Drawer menu items
  const menuItems = [
    { icon: 'mail', label: 'All Inboxes', mailbox: 'inbox' as const, count: emails.filter((e: Email) => !e.isRead).length },
    { icon: 'star', label: 'Starred', mailbox: 'starred' as const, count: emails.filter((e: Email) => e.isStarred).length },
    { icon: 'send', label: 'Sent', mailbox: 'sent' as const, count: 0 },
    { icon: 'document-text', label: 'Drafts', mailbox: 'drafts' as const, count: 0 },
    { icon: 'trash', label: 'Trash', mailbox: 'trash' as const, count: 0 },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor="white" />

      {/* Drawer Overlay */}
      {showDrawer && (
        <TouchableOpacity
          style={styles.drawerOverlay}
          activeOpacity={1}
          onPress={toggleDrawer}
        />
      )}

      {/* Side Drawer */}
      <Animated.View
        style={[
          styles.drawer,
          { transform: [{ translateX: drawerAnim }] },
        ]}
      >
        {/* Drawer Header */}
        <View style={styles.drawerHeader}>
          <Image
            source={require('../../assets/logo.png')}
            style={styles.drawerLogoImage}
            resizeMode="contain"
          />
        </View>

        {/* Menu Items */}
        <View style={styles.drawerMenu}>
          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.menuItem,
                currentMailbox === item.mailbox && styles.menuItemActive,
              ]}
              onPress={() => {
                setCurrentMailbox(item.mailbox);
                toggleDrawer();
              }}
            >
              <Ionicons
                name={item.icon as any}
                size={22}
                color={currentMailbox === item.mailbox ? colors.primary : '#5F6368'}
              />
              <Text
                style={[
                  styles.menuItemText,
                  currentMailbox === item.mailbox && styles.menuItemTextActive,
                ]}
              >
                {item.label}
              </Text>
              {item.count > 0 && (
                <Text style={styles.menuItemCount}>{item.count}</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* Encryption Levels Legend */}
        <View style={styles.encryptionLegend}>
          <Text style={styles.legendTitle}>Encryption Levels</Text>
          {[1, 2, 3, 4].map((level) => {
            const info = getEncryptionInfo(level as 1 | 2 | 3 | 4);
            return (
              <View key={level} style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: info?.color }]} />
                <Text style={styles.legendText}>Level {level} - {info?.label}</Text>
              </View>
            );
          })}
        </View>
      </Animated.View>

      {/* Main Content */}
      <View style={styles.mainContent}>
        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <TouchableOpacity onPress={toggleDrawer} style={styles.menuButton}>
            <Ionicons name="menu" size={24} color="#5F6368" />
          </TouchableOpacity>

          <View style={styles.searchBar}>
            <Ionicons name="search" size={20} color="#9AA0A6" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search in mail"
              placeholderTextColor="#9AA0A6"
              value={searchQuery}
              onChangeText={setSearchQuery}
            />
          </View>

          <TouchableOpacity
            style={styles.profileButton}
            onPress={() => setShowProfileMenu(!showProfileMenu)}
          >
            <View style={styles.profileAvatar}>
              <Text style={styles.profileAvatarText}>
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Profile Dropdown */}
        {showProfileMenu && (
          <View style={styles.profileDropdown}>
            <View style={styles.profileInfo}>
              <View style={styles.profileAvatarLarge}>
                <Text style={styles.profileAvatarTextLarge}>
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </Text>
              </View>
              <Text style={styles.profileName}>{user?.name || 'User'}</Text>
              <Text style={styles.profileEmail}>{user?.email || 'user@qumail.app'}</Text>
            </View>
            <TouchableOpacity
              style={styles.profileMenuItem}
              onPress={() => {
                setShowProfileMenu(false);
                navigation.navigate('Settings');
              }}
            >
              <Ionicons name="settings-outline" size={20} color="#5F6368" />
              <Text style={styles.profileMenuItemText}>Settings</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.profileMenuItem}
              onPress={() => {
                setShowProfileMenu(false);
                logout();
              }}
            >
              <Ionicons name="log-out-outline" size={20} color="#EA4335" />
              <Text style={[styles.profileMenuItemText, { color: '#EA4335' }]}>Sign out</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Inbox Label */}
        <View style={styles.inboxLabel}>
          <View style={styles.inboxLabelLeft}>
            <Text style={styles.inboxLabelText}>
              {currentMailbox.charAt(0).toUpperCase() + currentMailbox.slice(1)}
            </Text>
            {/* Demo Mode Badge */}
            <View style={[
              styles.connectionBadge,
              { backgroundColor: '#FF9800' }
            ]}>
              <Text style={styles.connectionBadgeText}>
                DEMO
              </Text>
            </View>
          </View>
          <Text style={styles.emailCount}>
            {filteredEmails.length} {filteredEmails.length === 1 ? 'message' : 'messages'}
          </Text>
        </View>

        {/* Loading indicator */}
        {isLoading && !refreshing && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={colors.primary} />
            <Text style={styles.loadingText}>Fetching emails...</Text>
          </View>
        )}

        {/* Error message */}
        {error && (
          <View style={styles.errorContainer}>
            <Ionicons name="warning-outline" size={16} color="#EA4335" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Email List */}
        <FlatList
          data={filteredEmails}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <EmailItem
              email={item}
              onPress={() => handleEmailPress(item.id)}
              onStarPress={() => toggleStar(item.id)}
            />
          )}
          contentContainerStyle={styles.emailList}
          showsVerticalScrollIndicator={false}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={[colors.primary]}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="mail-open-outline" size={64} color="#DADCE0" />
              <Text style={styles.emptyStateText}>
                {isLoading ? 'Loading emails...' : 'No emails found'}
              </Text>
            </View>
          }
        />

        {/* Floating Compose Button */}
        <TouchableOpacity style={styles.fab} onPress={handleCompose} activeOpacity={0.9}>
          <Ionicons name="pencil" size={22} color="white" />
          <Text style={styles.fabText}>Compose</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  mainContent: {
    flex: 1,
    backgroundColor: 'white',
  },

  // Search Bar
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: 'white',
  },
  menuButton: {
    padding: 8,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F3F4',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginHorizontal: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#202124',
    marginLeft: 12,
    padding: 0,
  },
  profileButton: {
    padding: 4,
  },
  profileAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileAvatarText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },

  // Profile Dropdown
  profileDropdown: {
    position: 'absolute',
    top: 60,
    right: 16,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    width: 250,
    zIndex: 1000,
    ...shadows.medium,
  },
  profileInfo: {
    alignItems: 'center',
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E8EAED',
    marginBottom: 8,
  },
  profileAvatarLarge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  profileAvatarTextLarge: {
    color: 'white',
    fontSize: 24,
    fontWeight: '600',
  },
  profileName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#202124',
    marginBottom: 2,
  },
  profileEmail: {
    fontSize: 13,
    color: '#5F6368',
  },
  profileMenuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
  },
  profileMenuItemText: {
    fontSize: 14,
    color: '#5F6368',
    marginLeft: 12,
  },

  // Inbox Label
  inboxLabel: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E8EAED',
  },
  inboxLabelLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  inboxLabelText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#5F6368',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  connectionBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  connectionBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: 'white',
    letterSpacing: 0.5,
  },
  emailCount: {
    fontSize: 12,
    color: '#9AA0A6',
  },

  // Loading and Error states
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    backgroundColor: '#F8F9FA',
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
    color: '#5F6368',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#FEE2E2',
    gap: 6,
  },
  errorText: {
    fontSize: 12,
    color: '#EA4335',
  },

  // Drawer
  drawerOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.4)',
    zIndex: 100,
  },
  drawer: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: SCREEN_WIDTH * 0.70,
    height: '100%',
    backgroundColor: 'white',
    zIndex: 101,
    paddingTop: 50,
  },
  drawerHeader: {
    paddingHorizontal: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E8EAED',
    alignItems: 'center',
  },
  drawerLogoImage: {
    width: 140,
    height: 70,
  },
  drawerLogo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  drawerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#202124',
    marginLeft: 10,
  },
  drawerSubtitle: {
    fontSize: 13,
    color: '#5F6368',
    marginTop: 4,
    marginLeft: 38,
  },
  drawerMenu: {
    paddingTop: 8,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 24,
    marginRight: 12,
    borderTopRightRadius: 25,
    borderBottomRightRadius: 25,
  },
  menuItemActive: {
    backgroundColor: colors.primary + '15',
  },
  menuItemText: {
    fontSize: 14,
    color: '#5F6368',
    marginLeft: 20,
    flex: 1,
    fontWeight: '500',
  },
  menuItemTextActive: {
    color: colors.primary,
    fontWeight: '600',
  },
  menuItemCount: {
    fontSize: 12,
    color: '#5F6368',
    fontWeight: '500',
  },

  // Encryption Legend
  encryptionLegend: {
    marginTop: 'auto',
    paddingHorizontal: 24,
    paddingVertical: 20,
    borderTopWidth: 1,
    borderTopColor: '#E8EAED',
  },
  legendTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#5F6368',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  legendText: {
    fontSize: 13,
    color: '#5F6368',
  },

  // Email List
  emailList: {
    paddingBottom: 100,
  },
  separator: {
    height: 1,
    backgroundColor: '#E8EAED',
    marginLeft: 76,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 100,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#9AA0A6',
    marginTop: 16,
  },

  // Email Item
  emailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: 'white',
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  encryptionBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'white',
  },
  emailContent: {
    flex: 1,
    marginLeft: 16,
    marginRight: 8,
  },
  emailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  senderName: {
    fontSize: 14,
    color: '#202124',
    flex: 1,
    marginRight: 8,
  },
  unreadText: {
    fontWeight: '700',
    color: '#000',
  },
  emailDate: {
    fontSize: 12,
    color: '#5F6368',
  },
  emailSubject: {
    fontSize: 13,
    color: '#202124',
    marginBottom: 2,
  },
  snippetRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  emailSnippet: {
    fontSize: 13,
    color: '#5F6368',
    flex: 1,
  },
  levelTag: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  levelTagText: {
    fontSize: 10,
    fontWeight: '700',
  },
  starButton: {
    padding: 8,
  },

  // FAB
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 16,
    ...shadows.medium,
    elevation: 4,
  },
  fabText: {
    color: 'white',
    fontSize: 15,
    fontWeight: '600',
    marginLeft: 8,
  },
});
