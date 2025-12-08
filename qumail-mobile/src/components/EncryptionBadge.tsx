import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, borderRadius } from '../constants/theme';
import { encryptionLevels } from '../constants/theme';

interface EncryptionBadgeProps {
  level: 1 | 2 | 3 | 4;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

export const EncryptionBadge: React.FC<EncryptionBadgeProps> = ({
  level,
  size = 'medium',
  showLabel = true,
}) => {
  const encryption = encryptionLevels.find((e) => e.level === level);
  if (!encryption) return null;

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          paddingHorizontal: 6,
          paddingVertical: 2,
          iconSize: 10,
          fontSize: 9,
        };
      case 'large':
        return {
          paddingHorizontal: 14,
          paddingVertical: 6,
          iconSize: 18,
          fontSize: 14,
        };
      default:
        return {
          paddingHorizontal: 10,
          paddingVertical: 4,
          iconSize: 14,
          fontSize: 11,
        };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: encryption.color + '20',
          borderColor: encryption.color + '40',
          paddingHorizontal: sizeStyles.paddingHorizontal,
          paddingVertical: sizeStyles.paddingVertical,
        },
      ]}
    >
      <Ionicons
        name={encryption.icon as any}
        size={sizeStyles.iconSize}
        color={encryption.color}
      />
      {showLabel && (
        <Text
          style={[
            styles.label,
            { color: encryption.color, fontSize: sizeStyles.fontSize },
          ]}
        >
          Level {level}: {encryption.shortName}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    gap: 6,
  },
  label: {
    fontWeight: '600',
  },
});
