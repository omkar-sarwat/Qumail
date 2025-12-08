import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  StatusBar,
  Alert,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, borderRadius, encryptionLevels } from '../constants/theme';
import { useAuthStore } from '../stores/authStore';

export const SettingsScreen: React.FC = () => {
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign Out', style: 'destructive', onPress: logout },
      ]
    );
  };

  const settingsSections = [
    {
      title: 'Account',
      items: [
        { icon: 'person-outline', label: 'Profile', value: user?.name },
        { icon: 'mail-outline', label: 'Email', value: user?.email },
        { icon: 'key-outline', label: 'Change Password', hasArrow: true },
      ],
    },
    {
      title: 'Security',
      items: [
        { icon: 'lock-closed-outline', label: 'Default Encryption', value: 'Level 1 (OTP)' },
        { icon: 'finger-print-outline', label: 'Biometric Lock', hasToggle: true, isEnabled: false },
        { icon: 'shield-checkmark-outline', label: 'Two-Factor Auth', hasArrow: true },
        { icon: 'time-outline', label: 'Auto-Lock', value: '5 minutes' },
      ],
    },
    {
      title: 'Notifications',
      items: [
        { icon: 'notifications-outline', label: 'Push Notifications', hasToggle: true, isEnabled: true },
        { icon: 'mail-unread-outline', label: 'New Email Alerts', hasToggle: true, isEnabled: true },
        { icon: 'volume-high-outline', label: 'Sound', hasToggle: true, isEnabled: false },
      ],
    },
    {
      title: 'Appearance',
      items: [
        { icon: 'moon-outline', label: 'Dark Mode', hasToggle: true, isEnabled: true },
        { icon: 'text-outline', label: 'Font Size', value: 'Medium' },
        { icon: 'color-palette-outline', label: 'Theme Color', value: 'Indigo' },
      ],
    },
    {
      title: 'About',
      items: [
        { icon: 'information-circle-outline', label: 'Version', value: '1.0.0' },
        { icon: 'document-text-outline', label: 'Terms of Service', hasArrow: true },
        { icon: 'shield-outline', label: 'Privacy Policy', hasArrow: true },
        { icon: 'help-circle-outline', label: 'Help & Support', hasArrow: true },
      ],
    },
  ];

  const renderSettingItem = (item: any, index: number, isLast: boolean) => (
    <TouchableOpacity
      key={index}
      style={[styles.settingItem, !isLast && styles.settingItemBorder]}
      activeOpacity={0.7}
    >
      <View style={styles.settingItemLeft}>
        <View style={styles.settingIcon}>
          <Ionicons name={item.icon} size={20} color={colors.primary} />
        </View>
        <Text style={styles.settingLabel}>{item.label}</Text>
      </View>
      <View style={styles.settingItemRight}>
        {item.value && <Text style={styles.settingValue}>{item.value}</Text>}
        {item.hasArrow && (
          <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
        )}
        {item.hasToggle && (
          <View
            style={[
              styles.toggleSwitch,
              item.isEnabled && styles.toggleSwitchActive,
            ]}
          >
            <View
              style={[
                styles.toggleKnob,
                item.isEnabled && styles.toggleKnobActive,
              ]}
            />
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* User Profile Card */}
        <LinearGradient
          colors={[colors.primary, colors.secondary]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.profileCard}
        >
          <View style={styles.profileAvatar}>
            {user?.picture ? (
              <Image source={{ uri: user.picture }} style={styles.avatarImage} />
            ) : (
              <Text style={styles.avatarText}>
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </Text>
            )}
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{user?.name || 'QuMail User'}</Text>
            <Text style={styles.profileEmail}>{user?.email || 'user@qumail.app'}</Text>
          </View>
          <TouchableOpacity style={styles.editButton}>
            <Ionicons name="pencil" size={18} color={colors.textPrimary} />
          </TouchableOpacity>
        </LinearGradient>

        {/* Encryption Levels Info */}
        <View style={styles.encryptionInfo}>
          <Text style={styles.sectionTitle}>Encryption Levels</Text>
          <View style={styles.encryptionGrid}>
            {encryptionLevels.map((level) => (
              <View key={level.level} style={styles.encryptionCard}>
                <View
                  style={[
                    styles.encryptionIconContainer,
                    { backgroundColor: level.color + '20' },
                  ]}
                >
                  <Ionicons
                    name={level.icon as any}
                    size={20}
                    color={level.color}
                  />
                </View>
                <Text style={styles.encryptionName}>{level.shortName}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Settings Sections */}
        {settingsSections.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.section}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <View style={styles.sectionContent}>
              {section.items.map((item, itemIndex) =>
                renderSettingItem(
                  item,
                  itemIndex,
                  itemIndex === section.items.length - 1
                )
              )}
            </View>
          </View>
        ))}

        {/* Sign Out Button */}
        <TouchableOpacity style={styles.signOutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={22} color={colors.error} />
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>QuMail v1.0.0</Text>
          <Text style={styles.footerSubtext}>Quantum-Secure Email</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    padding: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.backgroundSecondary,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  content: {
    flex: 1,
    padding: spacing.md,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.lg,
  },
  profileAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarImage: {
    width: 60,
    height: 60,
    borderRadius: 30,
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  profileInfo: {
    flex: 1,
    marginLeft: spacing.md,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  profileEmail: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
  },
  editButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  encryptionInfo: {
    marginBottom: spacing.lg,
  },
  encryptionGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  encryptionCard: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginHorizontal: spacing.xs,
  },
  encryptionIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  encryptionName: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionContent: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
  },
  settingItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  settingItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: colors.primary + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  settingLabel: {
    fontSize: 16,
    color: colors.textPrimary,
  },
  settingItemRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  settingValue: {
    fontSize: 14,
    color: colors.textMuted,
  },
  toggleSwitch: {
    width: 44,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.border,
    padding: 2,
  },
  toggleSwitchActive: {
    backgroundColor: colors.success,
  },
  toggleKnob: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.textPrimary,
  },
  toggleKnobActive: {
    transform: [{ translateX: 20 }],
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.error + '15',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  signOutText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.error,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    marginTop: spacing.lg,
  },
  footerText: {
    fontSize: 14,
    color: colors.textMuted,
    fontWeight: '500',
  },
  footerSubtext: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
});
