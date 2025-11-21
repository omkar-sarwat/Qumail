# QuMail Electron - Quick Reference Card

## 📋 Essential Commands

### Setup (Once)
```powershell
.\SETUP_ELECTRON.ps1
```

### Development
```powershell
.\START_ELECTRON_DEV.ps1
```

### Build Production
```powershell
.\BUILD_PYTHON_BUNDLES.ps1
.\BUILD_ELECTRON_APP.ps1
```

## 🗂️ Project Structure

```
qumail-secure-email/
├── qumail-frontend/          # Electron + React
│   ├── electron/             # Main & Preload
│   ├── src/                  # React app
│   ├── build/                # Icons
│   └── package.json
├── qumail-backend/           # FastAPI
│   └── qumail-backend.spec
├── next-door-key-simulator/  # KME
│   └── kme-server.spec
├── SETUP_ELECTRON.ps1        # Install deps
├── START_ELECTRON_DEV.ps1    # Dev mode
├── BUILD_PYTHON_BUNDLES.ps1  # Bundle Python
└── BUILD_ELECTRON_APP.ps1    # Build app
```

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `electron/main.ts` | Window manager, backend launcher, IPC |
| `electron/preload.ts` | Secure API bridge |
| `src/services/electronApi.ts` | Frontend API wrapper |
| `vite.config.ts` | Electron build config |
| `package.json` | Build scripts & config |
| `*.spec` | PyInstaller configs |

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```env
BACKEND_PORT=8000
KME1_URL=http://localhost:8010
KME2_URL=http://localhost:8020
```

**Frontend** (`.env`):
```env
VITE_API_URL=http://localhost:8000
```

### Ports
- Frontend: 5173 (dev)
- Backend: 8000
- KME1: 8010
- KME2: 8020

## 📦 Dependencies

### Frontend
- Electron 27.x
- React 18.x
- TypeScript 5.x
- Vite 5.x
- Zustand 4.x

### Backend
- Python 3.9-3.11
- FastAPI 0.104
- Uvicorn 0.24
- Cryptography 41.x

### Build Tools
- electron-builder
- PyInstaller
- vite-plugin-electron

## 🚀 npm Scripts

```powershell
cd qumail-frontend

# Development
npm run dev              # Vite dev server
npm run electron:dev     # Electron + Vite

# Building
npm run build            # Build frontend
npm run electron:build   # Build + package
npm run electron:dist    # All platforms
npm run electron:dist:win    # Windows only
npm run electron:dist:mac    # macOS only
npm run electron:dist:linux  # Linux only

# Testing
npm test                 # Run tests
npm run lint             # Lint code
```

## 🔍 Debugging

### Open DevTools
- Windows/Linux: `Ctrl + Shift + I`
- macOS: `Cmd + Option + I`

### Check Logs
```typescript
// Main process
console.log('[Main]', data)

// Renderer process
console.log('[Renderer]', data)
```

### Backend Logs
Visible in terminal where you started the app

## 🐛 Quick Fixes

### Backend won't start
```powershell
cd qumail-backend
python -m uvicorn app.main:app --port 8000
```

### Blank window
```powershell
cd qumail-frontend
Remove-Item -Recurse dist, dist-electron
npm run build
npm run electron:dev
```

### Build fails
```powershell
cd qumail-frontend
npm ci
npm run electron:build
```

## 📱 API Usage

### Frontend Code

```typescript
import { 
  makeBackendRequest, 
  showNotification,
  isElectron 
} from '@/services/electronApi'

// Check environment
if (isElectron()) {
  console.log('Running in Electron')
}

// Backend API
const emails = await makeBackendRequest(
  'GET', 
  '/api/v1/messages'
)

// Notification
await showNotification(
  'New Email', 
  'You have 3 unread messages'
)

// File dialog
const files = await openFileDialog({
  properties: ['openFile', 'multiSelections']
})
```

## 📁 Output Locations

### Development
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

### Production Build
- Windows: `qumail-frontend/release/*.exe`
- macOS: `qumail-frontend/release/*.dmg`
- Linux: `qumail-frontend/release/*.AppImage`

## 🔐 Security Levels

| Level | Algorithm | Key Source |
|-------|-----------|------------|
| 1 | OTP | Quantum (KME) |
| 2 | AES-256-GCM | Quantum-enhanced |
| 3 | PQC (Kyber/Dilithium) | Quantum-enhanced |
| 4 | RSA-4096 + AES | Quantum-enhanced |

## 🎨 Customization

### Change Icons
Place in `qumail-frontend/build/`:
- `icon.ico` (Windows)
- `icon.icns` (macOS)
- `icon.png` (Linux)

### App Name
Edit `package.json`:
```json
{
  "name": "your-app-name",
  "productName": "Your App Display Name"
}
```

## 📚 Documentation

- **Complete Guide**: `ELECTRON_APP_GUIDE.md`
- **Conversion Summary**: `ELECTRON_CONVERSION_SUMMARY.md`
- **Main README**: `ELECTRON_README.md`
- **Security Requirements**: `.github/instructions/instructon1.instructions.md`

## ✅ Testing Checklist

Before release:
- [ ] All 4 encryption levels work
- [ ] System tray functional
- [ ] Notifications appear
- [ ] File dialogs work
- [ ] Backend starts automatically
- [ ] App doesn't crash on close
- [ ] Built installer works
- [ ] Icons display correctly

## 🆘 Get Help

1. Check `ELECTRON_APP_GUIDE.md`
2. Review error logs
3. Try troubleshooting steps
4. Open GitHub issue

## 🎯 Quick Tips

💡 **Dev Mode**: Backend runs separately, faster restarts
💡 **Production**: Backend bundled inside app
💡 **Hot Reload**: Frontend changes reflect instantly
💡 **DevTools**: Always available in dev mode
💡 **System Tray**: Minimize instead of quit
💡 **Ctrl+C**: Stops all services cleanly

---

**Version**: 1.0.0  
**Updated**: November 17, 2025

For detailed information, see `ELECTRON_APP_GUIDE.md`
