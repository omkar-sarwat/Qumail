import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import {
  LoginScreen,
  InboxScreen,
  EmailDetailScreen,
  ComposeScreen,
  SettingsScreen,
} from '../screens';
import { colors } from '../constants/theme';
import { useAuthStore } from '../stores/authStore';

// Type definitions
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  EmailDetail: { emailId: string };
  Compose: undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

// Main App Navigator - No bottom tabs, clean stack navigation
export const AppNavigator: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      {!isAuthenticated ? (
        <Stack.Screen
          name="Auth"
          component={LoginScreen}
          options={{ animation: 'fade' }}
        />
      ) : (
        <>
          <Stack.Screen name="Main" component={InboxScreen} />
          <Stack.Screen
            name="EmailDetail"
            component={EmailDetailScreen}
            options={{
              animation: 'slide_from_right',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="Compose"
            component={ComposeScreen}
            options={{
              animation: 'slide_from_bottom',
              presentation: 'modal',
            }}
          />
          <Stack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{
              animation: 'slide_from_right',
              presentation: 'card',
            }}
          />
        </>
      )}
    </Stack.Navigator>
  );
};
