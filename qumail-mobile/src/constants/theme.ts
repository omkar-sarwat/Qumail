// QuMail Theme - "Modern 3D" Blue Design
export const colors = {
  // Primary Brand Color (The Blue Background)
  primary: '#2E71FE', // Vibrant Blue from the image
  primaryDark: '#1E5ADB',
  primaryLight: '#6094FE',
  
  // Secondary / Accents
  secondary: '#FFD336', // The yellow star color
  secondaryDark: '#F59E0B',
  accent: '#FF6B6B', 
  
  // Backgrounds
  background: '#2E71FE', // Main background is blue
  backgroundSecondary: '#F5F7FA',
  backgroundTertiary: '#E5E7EB',
  surface: '#FFFFFF', // The white sheet
  surfaceSubtle: '#F5F7FA', // Light gray for tags/backgrounds
  
  // Status
  success: '#10B981',
  error: '#EF4444',
  warning: '#F59E0B',
  info: '#3B82F6',
  
  // Text
  textPrimary: '#1A1E2D',
  textSecondary: '#6B7280',
  textMuted: '#9CA3AF',
  textInverse: '#FFFFFF',
  
  // Tags/Labels
  tags: {
    blue: { bg: '#EBF3FF', text: '#2E71FE' },
    darkBlue: { bg: '#2E71FE', text: '#FFFFFF' },
    purple: { bg: '#F3E8FF', text: '#9333EA' },
    green: { bg: '#ECFDF5', text: '#10B981' },
    orange: { bg: '#FFF7ED', text: '#F97316' },
  },

  // Encryption
  encryption: {
    level1: '#10B981',
    level2: '#3B82F6',
    level3: '#8B5CF6',
    level4: '#F59E0B',
  },
  
  border: '#E5E7EB',
  
  // Shadows
  shadow: '#000000',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32, // For the white sheet corners
  full: 9999,
};

export const typography = {
  h1: { fontSize: 32, fontWeight: '700' as const, color: colors.textInverse },
  h2: { fontSize: 24, fontWeight: '700' as const, color: colors.textPrimary },
  h3: { fontSize: 18, fontWeight: '600' as const, color: colors.textPrimary },
  body: { fontSize: 15, fontWeight: '400' as const, color: colors.textSecondary },
  caption: { fontSize: 13, fontWeight: '500' as const, color: colors.textMuted },
};

export const shadows = {
  soft: {
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  medium: {
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 5,
  },
  strong: {
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.25,
    shadowRadius: 25,
    elevation: 10,
  },
  // Aliases
  get sm() { return this.soft },
  get md() { return this.medium },
  get lg() { return this.strong },
};

export const encryptionLevels = [
  {
    level: 1 as const,
    name: 'OTP (One-Time Pad)',
    shortName: 'OTP',
    description: 'Quantum-secure one-time pad encryption',
    icon: 'shield-checkmark',
    color: colors.encryption.level1,
  },
  {
    level: 2 as const,
    name: 'AES-256-GCM',
    shortName: 'AES-256',
    description: 'Advanced Encryption Standard with quantum keys',
    icon: 'lock-closed',
    color: colors.encryption.level2,
  },
  {
    level: 3 as const,
    name: 'Post-Quantum Crypto',
    shortName: 'PQC',
    description: 'Kyber1024 + Dilithium5 algorithms',
    icon: 'diamond',
    color: colors.encryption.level3,
  },
  {
    level: 4 as const,
    name: 'RSA-4096 Hybrid',
    shortName: 'RSA-4096',
    description: 'RSA + AES hybrid with quantum enhancement',
    icon: 'key',
    color: colors.encryption.level4,
  },
];
