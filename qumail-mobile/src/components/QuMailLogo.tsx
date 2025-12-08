import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../constants/theme';

interface QuMailLogoProps {
  size?: number;
  showText?: boolean;
}

export const QuMailLogo: React.FC<QuMailLogoProps> = ({
  size = 80,
  showText = true,
}) => {
  const iconSize = size * 0.5;
  const borderRadius = size * 0.25;

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={[colors.primary, colors.secondary]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[
          styles.logoContainer,
          {
            width: size,
            height: size,
            borderRadius,
          },
        ]}
      >
        <Ionicons name="mail" size={iconSize} color={colors.textPrimary} />
        <View style={[styles.quantumDot, { top: size * 0.1, right: size * 0.1 }]}>
          <View style={styles.quantumDotInner} />
        </View>
      </LinearGradient>
      {showText && (
        <Text style={styles.logoText}>QuMail</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  quantumDot: {
    position: 'absolute',
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quantumDotInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.textPrimary,
  },
  logoText: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.textPrimary,
    marginTop: 12,
    letterSpacing: 1,
  },
});
