import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, borderRadius } from '../constants/theme';
import { encryptionLevels } from '../constants/theme';

interface EncryptionLevelSelectorProps {
  selectedLevel: 1 | 2 | 3 | 4;
  onSelect: (level: 1 | 2 | 3 | 4) => void;
}

export const EncryptionLevelSelector: React.FC<EncryptionLevelSelectorProps> = ({
  selectedLevel,
  onSelect,
}) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Encryption Level</Text>
      <View style={styles.grid}>
        {encryptionLevels.map((encryption) => (
          <TouchableOpacity
            key={encryption.level}
            style={[
              styles.levelCard,
              selectedLevel === encryption.level && {
                borderColor: encryption.color,
                backgroundColor: encryption.color + '15',
              },
            ]}
            onPress={() => onSelect(encryption.level)}
            activeOpacity={0.7}
          >
            <View
              style={[
                styles.iconContainer,
                { backgroundColor: encryption.color + '20' },
              ]}
            >
              <Ionicons
                name={encryption.icon as any}
                size={24}
                color={encryption.color}
              />
            </View>
            <Text
              style={[
                styles.levelTitle,
                selectedLevel === encryption.level && { color: encryption.color },
              ]}
            >
              Level {encryption.level}
            </Text>
            <Text style={styles.levelName}>{encryption.shortName}</Text>
            {selectedLevel === encryption.level && (
              <View
                style={[styles.checkmark, { backgroundColor: encryption.color }]}
              >
                <Ionicons name="checkmark" size={12} color="white" />
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.descriptionContainer}>
        <Ionicons
          name="information-circle"
          size={16}
          color={colors.textMuted}
        />
        <Text style={styles.description}>
          {encryptionLevels.find((e) => e.level === selectedLevel)?.description}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  levelCard: {
    flex: 1,
    minWidth: '45%',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    position: 'relative',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  levelTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  levelName: {
    fontSize: 12,
    color: colors.textMuted,
  },
  checkmark: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  descriptionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
    padding: spacing.sm,
    backgroundColor: colors.backgroundSecondary,
    borderRadius: borderRadius.sm,
    gap: spacing.sm,
  },
  description: {
    flex: 1,
    fontSize: 12,
    color: colors.textMuted,
  },
});
