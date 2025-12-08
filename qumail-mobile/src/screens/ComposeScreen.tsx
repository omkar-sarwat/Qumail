import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { LoadingSpinner } from '../components';
import { colors, shadows } from '../constants/theme';
import { useEmailStore } from '../stores/emailStore';

type RootStackParamList = {
  Inbox: undefined;
  EmailDetail: { emailId: string };
  Compose: undefined;
};

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

// Encryption level data
const encryptionLevels = [
  {
    level: 1 as const,
    name: 'OTP',
    fullName: 'One-Time Pad',
    description: 'Unbreakable quantum encryption',
    icon: 'shield-checkmark',
    color: '#10B981',
    gradient: ['#10B981', '#059669'] as const,
  },
  {
    level: 2 as const,
    name: 'AES-256',
    fullName: 'AES-256-GCM',
    description: 'Military-grade symmetric encryption',
    icon: 'lock-closed',
    color: '#3B82F6',
    gradient: ['#3B82F6', '#2563EB'] as const,
  },
  {
    level: 3 as const,
    name: 'PQC',
    fullName: 'Post-Quantum Crypto',
    description: 'Kyber1024 + Dilithium5',
    icon: 'diamond',
    color: '#8B5CF6',
    gradient: ['#8B5CF6', '#7C3AED'] as const,
  },
  {
    level: 4 as const,
    name: 'RSA-4096',
    fullName: 'RSA-4096 Hybrid',
    description: 'Asymmetric + quantum enhanced',
    icon: 'key',
    color: '#F59E0B',
    gradient: ['#F59E0B', '#D97706'] as const,
  },
];

export const ComposeScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const { sendEmail } = useEmailStore();

  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [encryptionLevel, setEncryptionLevel] = useState<1 | 2 | 3 | 4>(1);
  const [showEncryption, setShowEncryption] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const selectedEncryption = encryptionLevels.find(e => e.level === encryptionLevel)!;
  const isValid = to.trim().length > 0 && subject.trim().length > 0 && body.trim().length > 0;

  const handleSend = async () => {
    if (!isValid) {
      Alert.alert('Missing Fields', 'Please fill in all required fields.');
      return;
    }

    if (!to.includes('@')) {
      Alert.alert('Invalid Email', 'Please enter a valid email address.');
      return;
    }

    setIsSending(true);
    try {
      await sendEmail(to, subject, body, encryptionLevel);
      Alert.alert('✅ Sent Successfully', `Email encrypted with ${selectedEncryption.name} and sent!`, [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to send email. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  const handleDiscard = () => {
    if (to || subject || body) {
      Alert.alert(
        'Discard Draft?',
        'Are you sure you want to discard this email?',
        [
          { text: 'Keep Editing', style: 'cancel' },
          { text: 'Discard', style: 'destructive', onPress: () => navigation.goBack() },
        ]
      );
    } else {
      navigation.goBack();
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <KeyboardAvoidingView
          style={styles.keyboardView}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          {/* Modern Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={handleDiscard} style={styles.headerButton}>
              <Ionicons name="close" size={24} color="#374151" />
            </TouchableOpacity>
            
            <View style={styles.headerCenter}>
              <Text style={styles.headerTitle}>New Message</Text>
              <View style={[styles.encryptionChip, { backgroundColor: selectedEncryption.color + '20' }]}>
                <Ionicons name={selectedEncryption.icon as any} size={12} color={selectedEncryption.color} />
                <Text style={[styles.encryptionChipText, { color: selectedEncryption.color }]}>
                  {selectedEncryption.name}
                </Text>
              </View>
            </View>
            
            <TouchableOpacity 
              onPress={handleSend} 
              disabled={!isValid || isSending}
              style={styles.headerButton}
            >
              {isSending ? (
                <LoadingSpinner size="small" />
              ) : (
                <LinearGradient
                  colors={isValid ? ['#3B82F6', '#2563EB'] : ['#D1D5DB', '#9CA3AF']}
                  style={styles.sendButton}
                >
                  <Ionicons name="send" size={18} color="white" />
                </LinearGradient>
              )}
            </TouchableOpacity>
          </View>

          <ScrollView 
            style={styles.content} 
            contentContainerStyle={styles.contentContainer}
            keyboardShouldPersistTaps="handled"
          >
            {/* To Field */}
            <View style={styles.fieldContainer}>
              <View style={styles.fieldRow}>
                <Text style={styles.fieldLabel}>To</Text>
                <TextInput
                  style={styles.fieldInput}
                  value={to}
                  onChangeText={setTo}
                  placeholder="recipient@email.com"
                  placeholderTextColor="#9CA3AF"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
            </View>

            {/* Subject Field */}
            <View style={styles.fieldContainer}>
              <View style={styles.fieldRow}>
                <Text style={styles.fieldLabel}>Subject</Text>
                <TextInput
                  style={styles.fieldInput}
                  value={subject}
                  onChangeText={setSubject}
                  placeholder="What's this about?"
                  placeholderTextColor="#9CA3AF"
                />
              </View>
            </View>

            {/* Message Body - ABOVE encryption */}
            <View style={styles.bodyContainer}>
              <TextInput
                style={styles.bodyInput}
                value={body}
                onChangeText={setBody}
                placeholder="Write your message here..."
                placeholderTextColor="#9CA3AF"
                multiline
                textAlignVertical="top"
              />
            </View>

            {/* Encryption Section - Collapsible List */}
            <View style={styles.encryptionSection}>
              <TouchableOpacity 
                style={styles.encryptionHeader}
                onPress={() => setShowEncryption(!showEncryption)}
              >
                <View style={styles.encryptionHeaderLeft}>
                  <LinearGradient
                    colors={selectedEncryption.gradient}
                    style={styles.encryptionIcon}
                  >
                    <Ionicons name={selectedEncryption.icon as any} size={16} color="white" />
                  </LinearGradient>
                  <View>
                    <Text style={styles.encryptionTitle}>Security Level</Text>
                    <Text style={styles.encryptionSubtitle}>
                      {selectedEncryption.fullName}
                    </Text>
                  </View>
                </View>
                <Ionicons 
                  name={showEncryption ? "chevron-up" : "chevron-down"} 
                  size={20} 
                  color="#6B7280" 
                />
              </TouchableOpacity>

              {showEncryption && (
                <View style={styles.encryptionList}>
                  {encryptionLevels.map((enc) => (
                    <TouchableOpacity
                      key={enc.level}
                      style={[
                        styles.encryptionItem,
                        encryptionLevel === enc.level && styles.encryptionItemSelected,
                        encryptionLevel === enc.level && { borderColor: enc.color },
                      ]}
                      onPress={() => {
                        setEncryptionLevel(enc.level);
                        setShowEncryption(false);
                      }}
                    >
                      <LinearGradient
                        colors={enc.gradient}
                        style={styles.encryptionItemIcon}
                      >
                        <Ionicons name={enc.icon as any} size={18} color="white" />
                      </LinearGradient>
                      
                      <View style={styles.encryptionItemContent}>
                        <View style={styles.encryptionItemHeader}>
                          <Text style={styles.encryptionItemName}>{enc.name}</Text>
                          <Text style={[styles.encryptionItemLevel, { color: enc.color }]}>
                            Level {enc.level}
                          </Text>
                        </View>
                        <Text style={styles.encryptionItemDesc}>{enc.description}</Text>
                      </View>

                      {encryptionLevel === enc.level && (
                        <View style={[styles.checkMark, { backgroundColor: enc.color }]}>
                          <Ionicons name="checkmark" size={14} color="white" />
                        </View>
                      )}
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            {/* Quick Tips */}
            <View style={styles.tipsContainer}>
              <View style={styles.tipItem}>
                <Ionicons name="shield-checkmark" size={16} color="#10B981" />
                <Text style={styles.tipText}>End-to-end encrypted</Text>
              </View>
              <View style={styles.tipItem}>
                <Ionicons name="key" size={16} color="#3B82F6" />
                <Text style={styles.tipText}>Quantum key distribution</Text>
              </View>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  headerButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  encryptionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    gap: 4,
  },
  encryptionChipText: {
    fontSize: 11,
    fontWeight: '600',
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Content
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 40,
  },

  // Fields
  fieldContainer: {
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  fieldRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  fieldLabel: {
    width: 60,
    fontSize: 15,
    fontWeight: '500',
    color: '#6B7280',
  },
  fieldInput: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
    padding: 0,
  },

  // Body
  bodyContainer: {
    minHeight: 200,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  bodyInput: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
    lineHeight: 24,
    minHeight: 180,
  },

  // Encryption Section
  encryptionSection: {
    marginHorizontal: 16,
    marginTop: 8,
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  encryptionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  encryptionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  encryptionIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  encryptionTitle: {
    fontSize: 13,
    fontWeight: '500',
    color: '#6B7280',
  },
  encryptionSubtitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginTop: 1,
  },

  // Encryption List
  encryptionList: {
    padding: 8,
    paddingTop: 0,
    gap: 8,
  },
  encryptionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  encryptionItemSelected: {
    backgroundColor: '#FFFFFF',
    ...shadows.soft,
  },
  encryptionItemIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  encryptionItemContent: {
    flex: 1,
  },
  encryptionItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  encryptionItemName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  encryptionItemLevel: {
    fontSize: 12,
    fontWeight: '600',
  },
  encryptionItemDesc: {
    fontSize: 13,
    color: '#6B7280',
  },
  checkMark: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },

  // Tips
  tipsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
    paddingVertical: 20,
    marginTop: 8,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tipText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
});
