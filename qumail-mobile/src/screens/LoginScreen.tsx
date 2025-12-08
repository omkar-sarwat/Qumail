import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  StatusBar,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { GradientButton } from '../components';
import { colors, spacing, borderRadius } from '../constants/theme';
import { useAuthStore } from '../stores/authStore';

const { width } = Dimensions.get('window');

export const LoginScreen: React.FC = () => {
  const { login, setLoading, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [showEmailInput, setShowEmailInput] = useState(false);

  // Demo users for quick login
  const demoUsers = [
    { id: '1', name: 'Dr. Arun Sharma', email: 'arun.sharma@isro.gov.in', org: 'ISRO' },
    { id: '2', name: 'Priya Patel', email: 'priya.patel@drdo.gov.in', org: 'DRDO' },
    { id: '3', name: 'Rajesh Kumar', email: 'rajesh.kumar@nic.in', org: 'NIC' },
  ];

  const handleDemoLogin = (user: typeof demoUsers[0]) => {
    setLoading(true);
    
    setTimeout(() => {
      login(
        {
          id: user.id,
          email: user.email,
          name: user.name,
          picture: undefined,
        },
        'demo_session_token_' + user.id
      );
      setLoading(false);
    }, 800);
  };

  const handleCustomLogin = () => {
    if (!email.trim()) return;
    
    setLoading(true);
    
    setTimeout(() => {
      const name = email.split('@')[0].replace(/[._]/g, ' ');
      login(
        {
          id: 'custom_' + Date.now(),
          email: email.trim(),
          name: name.charAt(0).toUpperCase() + name.slice(1),
          picture: undefined,
        },
        'demo_session_token_custom'
      );
      setLoading(false);
    }, 800);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      {/* Background gradient */}
      <LinearGradient
        colors={[colors.background, colors.backgroundSecondary, colors.backgroundTertiary]}
        style={StyleSheet.absoluteFill}
      />
      
      {/* Decorative circles */}
      <View style={styles.circle1} />
      <View style={styles.circle2} />
      <View style={styles.circle3} />
      
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView 
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            {/* Logo Section */}
            <View style={styles.logoSection}>
              <View style={styles.logoContainer}>
                <Image
                  source={require('../../assets/logo.png')}
                  style={styles.logoImage}
                  resizeMode="contain"
                />
              </View>
              
              {/* Government Badges */}
              <View style={styles.badgeContainer}>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>🇮🇳 INDIA</Text>
                </View>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>🔒 SECURE</Text>
                </View>
              </View>
            </View>

            {/* Features Section */}
            <View style={styles.featuresSection}>
              <FeatureItem 
                icon="shield-checkmark" 
                color={colors.encryption.level1}
                title="OTP Encryption"
                desc="Unbreakable one-time pad"
              />
              <FeatureItem 
                icon="lock-closed" 
                color={colors.encryption.level2}
                title="AES-256 GCM"
                desc="Military-grade encryption"
              />
              <FeatureItem 
                icon="diamond" 
                color={colors.encryption.level3}
                title="Post-Quantum"
                desc="Future-proof cryptography"
              />
              <FeatureItem 
                icon="key" 
                color={colors.encryption.level4}
                title="Quantum Keys"
                desc="True random distribution"
              />
            </View>

            {/* Login Section */}
            <View style={styles.loginSection}>
              {!showEmailInput ? (
                <>
                  <Text style={styles.sectionTitle}>Quick Demo Login</Text>
                  
                  {demoUsers.map((user) => (
                    <TouchableOpacity
                      key={user.id}
                      style={styles.demoUserCard}
                      onPress={() => handleDemoLogin(user)}
                      disabled={isLoading}
                    >
                      <View style={styles.userAvatar}>
                        <Text style={styles.avatarText}>
                          {user.name.split(' ').map(n => n[0]).join('')}
                        </Text>
                      </View>
                      <View style={styles.userInfo}>
                        <Text style={styles.userName}>{user.name}</Text>
                        <Text style={styles.userEmail}>{user.email}</Text>
                      </View>
                      <View style={styles.orgBadge}>
                        <Text style={styles.orgText}>{user.org}</Text>
                      </View>
                    </TouchableOpacity>
                  ))}

                  <TouchableOpacity 
                    style={styles.customLoginLink}
                    onPress={() => setShowEmailInput(true)}
                  >
                    <Ionicons name="add-circle-outline" size={20} color={colors.primary} />
                    <Text style={styles.customLoginText}>Use custom email</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <Text style={styles.sectionTitle}>Enter Your Email</Text>
                  
                  <View style={styles.inputContainer}>
                    <Ionicons name="mail-outline" size={20} color={colors.textMuted} />
                    <TextInput
                      style={styles.input}
                      placeholder="your.email@example.com"
                      placeholderTextColor={colors.textMuted}
                      value={email}
                      onChangeText={setEmail}
                      keyboardType="email-address"
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                  </View>

                  <GradientButton
                    title="Continue"
                    onPress={handleCustomLogin}
                    loading={isLoading}
                    size="large"
                    disabled={!email.trim()}
                    style={styles.continueButton}
                  />

                  <TouchableOpacity 
                    style={styles.customLoginLink}
                    onPress={() => setShowEmailInput(false)}
                  >
                    <Ionicons name="arrow-back" size={20} color={colors.primary} />
                    <Text style={styles.customLoginText}>Back to demo accounts</Text>
                  </TouchableOpacity>
                </>
              )}
              
              <Text style={styles.disclaimer}>
                Demo mode • All data is simulated for demonstration
              </Text>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
};

// Feature Item Component
const FeatureItem: React.FC<{
  icon: string;
  color: string;
  title: string;
  desc: string;
}> = ({ icon, color, title, desc }) => (
  <View style={styles.featureItem}>
    <View style={[styles.featureIcon, { backgroundColor: color + '20' }]}>
      <Ionicons name={icon as any} size={18} color={color} />
    </View>
    <View style={styles.featureText}>
      <Text style={styles.featureTitle}>{title}</Text>
      <Text style={styles.featureDesc}>{desc}</Text>
    </View>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },
  
  // Decorative elements
  circle1: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: colors.primary + '10',
    top: -100,
    right: -100,
  },
  circle2: {
    position: 'absolute',
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: colors.secondary + '10',
    bottom: 100,
    left: -100,
  },
  circle3: {
    position: 'absolute',
    width: 150,
    height: 150,
    borderRadius: 75,
    backgroundColor: colors.accent + '10',
    bottom: 300,
    right: 50,
  },
  
  // Logo
  logoSection: {
    alignItems: 'center',
    paddingTop: spacing.xl,
    paddingBottom: spacing.lg,
  },
  logoContainer: {
    marginBottom: spacing.sm,
    alignItems: 'center',
  },
  logoImage: {
    width: 300,
    height: 150,
  },
  logoGradient: {
    width: 90,
    height: 90,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
  },
  appName: {
    fontSize: 36,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  tagline: {
    fontSize: 15,
    color: colors.textSecondary,
    letterSpacing: 1,
    marginBottom: spacing.md,
  },
  badgeContainer: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  badge: {
    backgroundColor: colors.primary + '20',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
  
  // Features
  featuresSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '48%',
    marginBottom: spacing.md,
    backgroundColor: colors.surface + '60',
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  featureIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  featureText: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  featureDesc: {
    fontSize: 10,
    color: colors.textMuted,
  },
  
  // Login
  loginSection: {
    flex: 1,
    paddingTop: spacing.md,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  demoUserCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  userAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primary + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  userEmail: {
    fontSize: 12,
    color: colors.textMuted,
  },
  orgBadge: {
    backgroundColor: colors.accent + '20',
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.sm,
  },
  orgText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.accent,
  },
  customLoginLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    gap: spacing.xs,
  },
  customLoginText: {
    fontSize: 14,
    color: colors.primary,
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: colors.textPrimary,
    marginLeft: spacing.sm,
    paddingVertical: spacing.sm,
  },
  continueButton: {
    marginBottom: spacing.sm,
  },
  disclaimer: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.lg,
  },
});
