import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  StatusBar,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { GradientButton, EncryptionBadge, LoadingSpinner } from '../components';
import { colors, spacing, borderRadius } from '../constants/theme';
import { useEmailStore } from '../stores/emailStore';
import { Email, Attachment } from '../types';

type RootStackParamList = {
  Inbox: undefined;
  EmailDetail: { emailId: string };
  Compose: undefined;
};

type EmailDetailRouteProp = RouteProp<RootStackParamList, 'EmailDetail'>;
type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

export const EmailDetailScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const route = useRoute<EmailDetailRouteProp>();
  const { emailId } = route.params;
  
  const { emails, selectedEmail, toggleStar, deleteEmail, decryptEmail } = useEmailStore();
  const [isDecrypting, setIsDecrypting] = useState(false);

  const email = selectedEmail || emails.find((e: Email) => e.id === emailId);

  if (!email) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Ionicons name="mail-unread-outline" size={60} color={colors.textMuted} />
          <Text style={styles.errorText}>Email not found</Text>
          <GradientButton
            title="Go Back"
            onPress={() => navigation.goBack()}
            variant="outline"
          />
        </View>
      </SafeAreaView>
    );
  }

  const handleDecrypt = async () => {
    setIsDecrypting(true);
    try {
      await decryptEmail(email.id);
    } catch (error) {
      Alert.alert('Decryption Failed', 'Unable to decrypt this email. Please try again.');
    } finally {
      setIsDecrypting(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Email',
      'Are you sure you want to delete this email?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            deleteEmail(email.id);
            navigation.goBack();
          },
        },
      ]
    );
  };

  const handleReply = () => {
    // Navigate to compose with reply data
    navigation.navigate('Compose');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const needsDecryption = email.isEncrypted && !email.isDecrypted;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor="white" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={() => toggleStar(email.id)} style={styles.headerButton}>
            <Ionicons
              name={email.isStarred ? 'star' : 'star-outline'}
              size={24}
              color={email.isStarred ? colors.warning : colors.textPrimary}
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={handleDelete} style={styles.headerButton}>
            <Ionicons name="trash-outline" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton}>
            <Ionicons name="ellipsis-vertical" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Subject */}
        <Text style={styles.subject}>{email.subject}</Text>

        {/* Encryption Badge */}
        {email.isEncrypted && email.encryptionLevel && (
          <View style={styles.encryptionRow}>
            <EncryptionBadge level={email.encryptionLevel} size="medium" />
            {email.isDecrypted && (
              <View style={styles.decryptedBadge}>
                <Ionicons name="checkmark-circle" size={14} color={colors.success} />
                <Text style={styles.decryptedText}>Decrypted</Text>
              </View>
            )}
          </View>
        )}

        {/* Sender Info */}
        <View style={styles.senderCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {email.from.name.charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.senderInfo}>
            <Text style={styles.senderName}>{email.from.name}</Text>
            <Text style={styles.senderEmail}>{email.from.email}</Text>
            <Text style={styles.date}>{formatDate(email.date)}</Text>
          </View>
        </View>

        {/* Recipient */}
        <View style={styles.recipientRow}>
          <Text style={styles.recipientLabel}>To:</Text>
          <Text style={styles.recipientValue}>
            {email.to.map((r: { name: string; email: string }) => r.email).join(', ')}
          </Text>
        </View>

        {/* Attachments */}
        {email.hasAttachments && email.attachments && (
          <View style={styles.attachmentsSection}>
            <Text style={styles.attachmentsTitle}>
              <Ionicons name="attach" size={16} color={colors.textSecondary} /> Attachments
            </Text>
            {email.attachments.map((attachment: Attachment) => (
              <TouchableOpacity key={attachment.id} style={styles.attachmentItem}>
                <Ionicons name="document" size={20} color={colors.primary} />
                <View style={styles.attachmentInfo}>
                  <Text style={styles.attachmentName}>{attachment.filename}</Text>
                  <Text style={styles.attachmentSize}>
                    {(attachment.size / 1024 / 1024).toFixed(2)} MB
                  </Text>
                </View>
                <Ionicons name="download-outline" size={20} color={colors.primary} />
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Email Body */}
        <View style={styles.bodySection}>
          {needsDecryption ? (
            <View style={styles.encryptedContent}>
              <View style={styles.lockContainer}>
                <Ionicons name="lock-closed" size={50} color={colors.warning} />
              </View>
              <Text style={styles.encryptedTitle}>Encrypted Message</Text>
              <Text style={styles.encryptedDescription}>
                This email is protected with Level {email.encryptionLevel} encryption.
                {'\n'}Click below to decrypt and view the content.
              </Text>
              
              {isDecrypting ? (
                <View style={styles.decryptingContainer}>
                  <View style={styles.decryptingAnimation}>
                    <Ionicons name="sync" size={40} color={colors.primary} />
                  </View>
                  <Text style={styles.decryptingText}>Decrypting with Quantum Keys...</Text>
                  <Text style={styles.decryptingSubtext}>Fetching keys from KME server</Text>
                </View>
              ) : (
                <GradientButton
                  title="🔓 Decrypt Message"
                  onPress={handleDecrypt}
                  style={styles.decryptButton}
                />
              )}
            </View>
          ) : (
            <Text style={styles.bodyText}>
              {email.decryptedBody || email.body}
            </Text>
          )}
        </View>
      </ScrollView>

      {/* Reply FAB */}
      <TouchableOpacity style={styles.replyFab} onPress={handleReply} activeOpacity={0.8}>
        <Ionicons name="arrow-undo" size={24} color={colors.textPrimary} />
        <Text style={styles.replyText}>Reply</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: 'white',
  },
  backButton: {
    padding: spacing.xs,
  },
  headerActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  headerButton: {
    padding: spacing.xs,
  },
  content: {
    flex: 1,
    padding: spacing.md,
  },
  subject: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  encryptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  decryptedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  decryptedText: {
    fontSize: 12,
    color: colors.success,
    fontWeight: '500',
  },
  senderCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  avatarText: {
    fontSize: 20,
    fontWeight: '600',
    color: 'white',
  },
  senderInfo: {
    flex: 1,
  },
  senderName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  senderEmail: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: 4,
  },
  date: {
    fontSize: 12,
    color: colors.textMuted,
  },
  recipientRow: {
    flexDirection: 'row',
    marginBottom: spacing.md,
    paddingHorizontal: spacing.sm,
  },
  recipientLabel: {
    fontSize: 14,
    color: colors.textMuted,
    marginRight: spacing.sm,
  },
  recipientValue: {
    fontSize: 14,
    color: colors.textSecondary,
    flex: 1,
  },
  attachmentsSection: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  attachmentsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  attachmentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  attachmentInfo: {
    flex: 1,
    marginLeft: spacing.sm,
  },
  attachmentName: {
    fontSize: 14,
    color: colors.textPrimary,
  },
  attachmentSize: {
    fontSize: 12,
    color: colors.textMuted,
  },
  bodySection: {
    marginTop: spacing.md,
    marginBottom: 100,
  },
  encryptedContent: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.warning + '40',
  },
  lockContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.warning + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  encryptedTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  encryptedDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
    lineHeight: 22,
  },
  decryptingContainer: {
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  decryptingAnimation: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  decryptingText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  decryptingSubtext: {
    fontSize: 14,
    color: colors.textMuted,
  },
  decryptButton: {
    marginTop: spacing.sm,
  },
  bodyText: {
    fontSize: 16,
    color: colors.textPrimary,
    lineHeight: 26,
  },
  replyFab: {
    position: 'absolute',
    bottom: spacing.lg,
    right: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
    gap: spacing.sm,
    elevation: 8,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  replyText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  errorText: {
    fontSize: 18,
    color: colors.textSecondary,
    marginVertical: spacing.lg,
  },
});
