# QuMail Electron App - Complete Guide

## Overview

QuMail is now a complete Electron desktop application with embedded Python backend services. The app bundles:

- **Frontend**: React + TypeScript UI running in Electron renderer
- **Backend**: FastAPI Python server embedded in the app
- **KME Servers**: Two quantum key management servers for encryption
- **Native Features**: System tray, notifications, file dialogs, menu bar

## Architecture

```
QuMail Electron App
├── Main Process (Node.js)
│   ├── Window Management
│   ├── System Tray & Menus
│   ├── IPC Communication
│   └── Python Process Manager
│       ├── Backend Server (FastAPI)
│       └── KME Servers (x2)
├── Renderer Process (Chromium)
│   └── React Frontend
└── Preload Script
    └── Secure IPC Bridge
```

## Prerequisites

### Development

- **Node.js** 18+ (with npm)
- **Python** 3.9-3.11
- **Git** (for version control)

### Building Production

- **PyInstaller** (for bundling Python)
- **electron-builder** (for packaging)
- Platform-specific tools:
  - Windows: Visual Studio Build Tools
  - macOS: Xcode Command Line Tools
  - Linux: Standard build tools

## Installation

### 1. Install Dependencies

```powershell
# Frontend dependencies
cd qumail-frontend
npm install

# Backend dependencies
cd ../qumail-backend
pip install -r requirements.txt

# KME dependencies
cd ../next-door-key-simulator
pip install -r requirements.txt
```

### 2. Install Build Tools

```powershell
# PyInstaller for bundling Python
pip install pyinstaller

# Verify installations
python --version
node --version
npm --version
```

## Development Mode

### Quick Start

```powershell
# From project root
.\START_ELECTRON_DEV.ps1
```

This script:
1. Starts KME1 on port 8010
2. Starts KME2 on port 8020
3. Starts Backend on port 8000
4. Launches Vite dev server on port 5173
5. Opens Electron app with hot-reload

### Manual Start

```powershell
# Terminal 1: KME1
cd next-door-key-simulator
$env:KME_PORT="8010"; $env:KME_ID="KME1"; python app.py

# Terminal 2: KME2
cd next-door-key-simulator
$env:KME_PORT="8020"; $env:KME_ID="KME2"; python app.py

# Terminal 3: Backend
cd qumail-backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 4: Electron
cd qumail-frontend
npm run electron:dev
```

### Development Features

- **Hot Reload**: Frontend changes reload automatically
- **DevTools**: Open with `Ctrl+Shift+I` or `Cmd+Option+I`
- **Backend Logs**: Visible in terminal
- **Console Logs**: Check main process and renderer logs

## Building Production App

### Step 1: Bundle Python Services

```powershell
# Creates standalone Python executables
.\BUILD_PYTHON_BUNDLES.ps1
```

This creates:
- `qumail-backend/dist/qumail-backend/` - Backend executable
- `next-door-key-simulator/dist/kme-server/` - KME executable

### Step 2: Build Electron App

```powershell
# Builds complete Electron application
.\BUILD_ELECTRON_APP.ps1
```

Or manually:

```powershell
cd qumail-frontend

# Windows
npm run electron:dist:win

# macOS
npm run electron:dist:mac

# Linux
npm run electron:dist:linux

# All platforms
npm run electron:dist
```

### Output

Built applications are in `qumail-frontend/release/`:

- **Windows**: `QuMail Secure Email Setup.exe` (NSIS installer)
- **macOS**: `QuMail Secure Email.dmg` (DMG image)
- **Linux**: `QuMail-Secure-Email.AppImage` (AppImage)

## Project Structure

```
qumail-secure-email/
├── qumail-frontend/
│   ├── electron/
│   │   ├── main.ts              # Main process (window, IPC, backend manager)
│   │   └── preload.ts           # Secure bridge between main & renderer
│   ├── src/
│   │   ├── services/
│   │   │   └── electronApi.ts   # Electron API wrapper
│   │   ├── components/          # React components
│   │   └── stores/              # State management
│   ├── build/                   # Icons and resources
│   ├── dist/                    # Built frontend
│   ├── dist-electron/           # Built Electron main/preload
│   ├── release/                 # Final packaged apps
│   ├── vite.config.ts           # Vite + Electron config
│   └── package.json             # Dependencies & build scripts
├── qumail-backend/
│   ├── app/                     # FastAPI application
│   ├── qumail-backend.spec      # PyInstaller config
│   └── requirements.txt
├── next-door-key-simulator/
│   ├── server/                  # KME server code
│   ├── kme-server.spec          # PyInstaller config
│   └── requirements.txt
├── certs/                       # SSL certificates
├── BUILD_PYTHON_BUNDLES.ps1     # Bundle Python to exe
├── BUILD_ELECTRON_APP.ps1       # Build Electron app
└── START_ELECTRON_DEV.ps1       # Dev mode launcher
```

## Key Features

### 1. Embedded Backend

Python backend runs as child process:
- **Development**: Separate Python process with reload
- **Production**: Bundled executable launched by Electron

### 2. IPC Communication

Type-safe communication between renderer and main:

```typescript
// Frontend usage
import { makeBackendRequest } from '@/services/electronApi'

const emails = await makeBackendRequest('GET', '/api/v1/messages')
```

### 3. Native Features

#### System Tray
- Minimize to tray on close
- Quick actions menu
- System notifications

#### Application Menu
- File → New Email (Ctrl+N)
- Edit → Copy/Paste
- View → DevTools, Zoom
- Window → Minimize, Hide to Tray

#### File Dialogs
```typescript
import { openFileDialog, saveFileDialog } from '@/services/electronApi'

const files = await openFileDialog({
  properties: ['openFile', 'multiSelections']
})
```

#### Notifications
```typescript
import { showNotification } from '@/services/electronApi'

await showNotification('New Email', 'You have 3 unread messages')
```

### 4. Security

- **Context Isolation**: Enabled for security
- **Node Integration**: Disabled in renderer
- **Preload Script**: Exposes only safe APIs
- **CSP Headers**: Content Security Policy enforced
- **Code Signing**: Configure for production

## Configuration

### Electron Builder (`package.json`)

```json
{
  "build": {
    "appId": "com.qumail.secure-email",
    "productName": "QuMail Secure Email",
    "extraResources": [
      "qumail-backend",
      "next-door-key-simulator",
      "certs"
    ]
  }
}
```

### Environment Variables

Development (`.env`):
```env
VITE_API_URL=http://localhost:8000
BACKEND_PORT=8000
KME1_PORT=8010
KME2_PORT=8020
```

### Vite Config

```typescript
export default defineConfig({
  plugins: [
    react(),
    electron([...]),
    renderer(),
  ],
  base: './',  // Relative paths for Electron
})
```

## Troubleshooting

### Backend Doesn't Start

**Issue**: "Backend server failed to start"

**Solution**:
```powershell
# Check Python path
python --version

# Test backend manually
cd qumail-backend
python -m uvicorn app.main:app --port 8000

# Check logs in Electron DevTools console
```

### Electron Window Blank

**Issue**: White screen on launch

**Solution**:
1. Open DevTools (`Ctrl+Shift+I`)
2. Check console for errors
3. Verify frontend built: `npm run build`
4. Clear cache: Delete `dist/` and rebuild

### Build Fails

**Issue**: `electron-builder` or `PyInstaller` fails

**Solution**:
```powershell
# Clear build artifacts
Remove-Item -Recurse dist, dist-electron, release, build

# Reinstall dependencies
npm ci
pip install -r requirements.txt --force-reinstall

# Rebuild
npm run build
npm run electron:dist
```

### Python Bundle Missing Modules

**Issue**: "Module not found" in production

**Solution**:
Edit `.spec` file and add to `hiddenimports`:
```python
hiddenimports = [
    'missing_module_name',
    # ...
]
```

## Code Signing (Production)

### Windows

1. Obtain code signing certificate
2. Configure in `package.json`:
```json
{
  "build": {
    "win": {
      "certificateFile": "path/to/cert.pfx",
      "certificatePassword": "password"
    }
  }
}
```

### macOS

1. Enroll in Apple Developer Program
2. Create signing certificate
3. Configure:
```json
{
  "build": {
    "mac": {
      "identity": "Developer ID Application: Your Name (XXXXXXXXXX)"
    }
  }
}
```

### Auto-Updates

Add `electron-updater` for automatic updates:

```powershell
npm install electron-updater
```

Configure in `main.ts`:
```typescript
import { autoUpdater } from 'electron-updater'

app.whenReady().then(() => {
  autoUpdater.checkForUpdatesAndNotify()
})
```

## Performance Optimization

### Frontend

- Code splitting with dynamic imports
- Lazy load components
- Optimize bundle size

### Backend

- Use PyInstaller's `--onefile` for smaller size
- Strip debug symbols
- Compress with UPX

### Electron

- Enable `asar` packaging
- Minimize `extraResources`
- Use `electron-builder` compression

## Testing

### Unit Tests

```powershell
# Frontend tests
cd qumail-frontend
npm test

# Backend tests
cd qumail-backend
pytest
```

### E2E Tests

Use Spectron or Playwright for Electron:

```powershell
npm install --save-dev spectron
```

## Deployment

### Distribution

1. **Direct Download**: Host `.exe`, `.dmg`, `.AppImage` files
2. **Auto-Updates**: Use `electron-updater` + release server
3. **App Stores**: Publish to Microsoft Store, Mac App Store

### CI/CD

GitHub Actions example:

```yaml
name: Build Electron App
on: [push]
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: actions/setup-python@v4
      - run: npm ci
      - run: npm run electron:dist
```

## Support

### Logs Location

- **Windows**: `%APPDATA%\QuMail Secure Email\logs`
- **macOS**: `~/Library/Logs/QuMail Secure Email`
- **Linux**: `~/.config/QuMail Secure Email/logs`

### Debug Mode

Set environment variable:
```powershell
$env:DEBUG="*"; npm run electron:dev
```

### Community

- GitHub Issues: Report bugs
- Discussions: Ask questions
- Documentation: https://github.com/yourusername/qumail

## License

See LICENSE file for details.

## Credits

- Electron Framework
- React + Vite
- FastAPI
- Next Door Key Simulator (ETSI QKD 014)
