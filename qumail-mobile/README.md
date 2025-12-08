# QuMail Mobile - Quantum-Secure Email App

A modern, sleek mobile email client with quantum encryption support. Built with React Native and Expo for iOS and Android.

## ✨ Features

### 🔐 Quantum Encryption Levels
- **Level 1 (OTP)**: One-Time Pad - Unbreakable quantum-secure encryption
- **Level 2 (AES-256-GCM)**: Military-grade AES encryption with quantum keys
- **Level 3 (PQC)**: Post-Quantum Cryptography - Kyber1024 + Dilithium5
- **Level 4 (RSA-4096)**: Hybrid RSA + AES with quantum enhancement

### 📱 Modern UI/UX
- Dark theme with beautiful gradients
- Smooth animations and transitions
- Intuitive navigation with bottom tabs
- Pull-to-refresh and seamless scrolling
- Encryption level badges and indicators

### ✉️ Email Features
- Inbox, Sent, Starred, and Drafts folders
- Email composition with encryption selection
- Attachment support
- Search functionality
- Mark as read/unread
- Star/unstar emails

### 🔒 Security
- Google OAuth authentication
- Secure token storage
- Biometric lock support (Face ID / Fingerprint)
- End-to-end encrypted email viewing

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Expo Go app on your phone (for development)

### Installation

```bash
# Navigate to the mobile app directory
cd qumail-mobile

# Install dependencies
npm install

# Start the development server
npx expo start
```

### Running on Device

1. Install **Expo Go** app from App Store (iOS) or Play Store (Android)
2. Run `npx expo start` in the terminal
3. Scan the QR code with:
   - iOS: Camera app
   - Android: Expo Go app

### Running on Simulator/Emulator

```bash
# iOS Simulator (macOS only)
npx expo run:ios

# Android Emulator
npx expo run:android
```

## 📁 Project Structure

```
qumail-mobile/
├── App.tsx                 # Main app entry point
├── app.json               # Expo configuration
├── babel.config.js        # Babel configuration
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── EmailListItem.tsx
│   │   ├── EncryptionBadge.tsx
│   │   ├── EncryptionLevelSelector.tsx
│   │   ├── GradientButton.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── QuMailLogo.tsx
│   │   └── SplashScreen.tsx
│   ├── constants/         # Theme and constants
│   │   └── theme.ts
│   ├── data/              # Mock data for development
│   │   └── mockEmails.ts
│   ├── navigation/        # Navigation configuration
│   │   └── AppNavigator.tsx
│   ├── screens/           # App screens
│   │   ├── ComposeScreen.tsx
│   │   ├── EmailDetailScreen.tsx
│   │   ├── InboxScreen.tsx
│   │   ├── LoginScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── services/          # API services
│   │   ├── api.ts
│   │   └── config.ts
│   ├── stores/            # Zustand state management
│   │   ├── authStore.ts
│   │   └── emailStore.ts
│   └── types/             # TypeScript types
│       └── index.ts
└── assets/                # Images and icons
```

## 🎨 Design System

### Colors
- **Primary**: Indigo (#6366F1)
- **Secondary**: Purple (#8B5CF6)
- **Accent**: Cyan (#06B6D4)
- **Background**: Dark Navy (#0F0F23)

### Encryption Level Colors
- Level 1 (OTP): Green (#10B981)
- Level 2 (AES): Blue (#3B82F6)
- Level 3 (PQC): Purple (#8B5CF6)
- Level 4 (RSA): Amber (#F59E0B)

## 🔧 Configuration

### Backend Connection
Update `src/services/config.ts` to change the backend URL:

```typescript
export const API_CONFIG = {
  BASE_URL: 'https://qumail-backend-gwec.onrender.com',
  // ...
};
```

### Google OAuth
The Google Client ID is configured in `app.json`:

```json
{
  "expo": {
    "extra": {
      "googleClientId": "your-client-id.apps.googleusercontent.com"
    }
  }
}
```

## 📦 Key Dependencies

- **@react-navigation**: Navigation library
- **expo-linear-gradient**: Gradient backgrounds
- **expo-secure-store**: Secure token storage
- **zustand**: State management
- **@expo/vector-icons**: Icon library
- **react-native-reanimated**: Animations

## 🔐 Connecting to Real Backend

Currently the app uses mock data for demonstration. To connect to the real QuMail backend:

1. Ensure the backend is running at `https://qumail-backend-gwec.onrender.com`
2. Update the auth store to use real Google OAuth via `expo-auth-session`
3. Replace mock email data with API calls in the email store

## 📱 Building for Production

### iOS
```bash
# Build for iOS
eas build --platform ios
```

### Android
```bash
# Build for Android
eas build --platform android
```

### Both Platforms
```bash
eas build --platform all
```

## 🐛 Troubleshooting

### Common Issues

1. **Metro bundler cache**: Clear with `npx expo start -c`
2. **Node modules**: Delete `node_modules` and run `npm install`
3. **iOS pods**: Run `cd ios && pod install`

### Development Tips

- Use React Native Debugger for debugging
- Enable Fast Refresh for quick development
- Use Expo Go for quick testing on device

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**QuMail** - Quantum-Secure Email for Everyone 🔒✉️
