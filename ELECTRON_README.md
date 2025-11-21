# 🚀 QuMail Secure Email - Electron Desktop Application

[![Electron](https://img.shields.io/badge/Electron-27.x-47848F?style=for-the-badge&logo=electron&logoColor=white)](https://www.electronjs.org/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

> **Quantum-Secure Email Client with Post-Quantum Cryptography and ETSI QKD 014 Integration**

QuMail is a complete desktop application that provides enterprise-grade email security with quantum-resistant encryption. Built with Electron, it combines a modern React frontend with a powerful Python backend, all packaged into a native desktop experience.

## ✨ Features

### 🔒 Quantum-Secure Encryption
- **4 Security Levels**: OTP, AES-256-GCM, Post-Quantum (Kyber/Dilithium), RSA-4096
- **ETSI QKD 014**: Compliant quantum key distribution
- **Hybrid Encryption**: Quantum + traditional cryptography
- **End-to-End**: Messages encrypted before transmission

### 🖥️ Native Desktop Experience
- **System Tray**: Minimize to tray, quick actions
- **Notifications**: Native OS notifications for new emails
- **File Dialogs**: Native file picker for attachments
- **Menu Bar**: Standard application menus
- **Offline Mode**: Works without internet (local encryption)

### 🎨 Modern UI/UX
- **Dark/Light Themes**: Automatic theme detection
- **Responsive Design**: Optimized for all screen sizes
- **Hot Reload**: Instant updates during development
- **Smooth Animations**: Framer Motion powered

### 🔐 Security First
- **Context Isolation**: Renderer process sandboxed
- **No Node Integration**: Zero exposure of Node APIs
- **Code Signing**: Production builds signed (configurable)
- **Auto Updates**: Optional update mechanism

### 📧 Email Management
- **Gmail Integration**: Full Google OAuth support
- **Multiple Accounts**: Switch between accounts
- **Rich Text Editor**: TipTap based composer
- **Attachments**: Secure file handling
- **Search**: Fast email search

## 📦 Quick Start

### Installation

```powershell
# Clone repository
git clone https://github.com/yourusername/qumail-secure-email.git
cd qumail-secure-email

# Run setup (installs all dependencies)
.\SETUP_ELECTRON.ps1
```

### Development Mode

```powershell
# Start all services and launch Electron app
.\START_ELECTRON_DEV.ps1
```

This starts:
- KME1 server (port 8010)
- KME2 server (port 8020)
- FastAPI backend (port 8000)
- Vite dev server (port 5173)
- Electron app with DevTools

### Build Production App

```powershell
# Step 1: Bundle Python services
.\BUILD_PYTHON_BUNDLES.ps1

# Step 2: Build Electron app
.\BUILD_ELECTRON_APP.ps1

# Output: qumail-frontend/release/
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           Electron Main Process                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Window Manager                           │  │
│  │  • BrowserWindow lifecycle                │  │
│  │  • Menu bar & System tray                 │  │
│  │  • Native dialogs & notifications         │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Python Backend Manager                   │  │
│  │  • FastAPI server (child process)         │  │
│  │  • KME1 & KME2 servers                    │  │
│  │  • Process lifecycle management           │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  IPC Handlers                             │  │
│  │  • Backend API proxy                      │  │
│  │  • File operations                        │  │
│  │  • System integration                     │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      │
                      │ IPC Bridge
                      ▼
┌─────────────────────────────────────────────────┐
│       Preload Script (Context Bridge)           │
│  • Exposes safe APIs to renderer                │
│  • Type-safe IPC communication                  │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         Electron Renderer Process               │
│  ┌──────────────────────────────────────────┐  │
│  │  React Frontend                           │  │
│  │  • Modern UI with TypeScript              │  │
│  │  • Zustand state management               │  │
│  │  │  React Router navigation                │  │
│  │  • TipTap rich text editor                │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
qumail-secure-email/
├── qumail-frontend/              # Electron + React frontend
│   ├── electron/
│   │   ├── main.ts              # Main process
│   │   └── preload.ts           # Preload script
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── services/
│   │   │   └── electronApi.ts   # Electron API wrapper
│   │   ├── stores/              # Zustand stores
│   │   └── types/               # TypeScript types
│   ├── build/                   # Icons & resources
│   ├── vite.config.ts           # Vite + Electron config
│   └── package.json             # Dependencies & scripts
│
├── qumail-backend/              # FastAPI backend
│   ├── app/                     # Application code
│   │   ├── main.py              # FastAPI app
│   │   ├── api/                 # API routes
│   │   ├── services/            # Business logic
│   │   └── models/              # Data models
│   ├── qumail-backend.spec      # PyInstaller config
│   └── requirements.txt
│
├── next-door-key-simulator/     # ETSI QKD 014 KME
│   ├── server/                  # KME server
│   ├── kme-server.spec          # PyInstaller config
│   └── requirements.txt
│
├── certs/                       # SSL certificates
│
├── SETUP_ELECTRON.ps1           # Quick setup script
├── START_ELECTRON_DEV.ps1       # Dev mode launcher
├── BUILD_PYTHON_BUNDLES.ps1     # Bundle Python → exe
├── BUILD_ELECTRON_APP.ps1       # Build Electron app
└── ELECTRON_APP_GUIDE.md        # Complete guide
```

## 🛠️ Technologies

### Frontend
- **Electron** 27.x - Desktop framework
- **React** 18.x - UI library
- **TypeScript** 5.x - Type safety
- **Vite** 5.x - Build tool
- **Zustand** 4.x - State management
- **TailwindCSS** 3.x - Styling
- **Framer Motion** 10.x - Animations

### Backend
- **Python** 3.9-3.11
- **FastAPI** 0.104 - Web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **Cryptography** - Encryption library
- **liboqs-python** - Post-quantum crypto

### Build Tools
- **electron-builder** - App packaging
- **PyInstaller** - Python bundling
- **vite-plugin-electron** - Vite integration

## 📋 System Requirements

### Development
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Node.js**: 18.x or higher
- **Python**: 3.9-3.11
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB free space

### Production (Built App)
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **RAM**: 2GB minimum
- **Disk**: 500MB free space

## 🚀 Available Scripts

### Development

```powershell
# Install all dependencies
.\SETUP_ELECTRON.ps1

# Start dev mode (all services)
.\START_ELECTRON_DEV.ps1

# Frontend only
cd qumail-frontend
npm run dev

# Electron dev mode
cd qumail-frontend
npm run electron:dev
```

### Building

```powershell
# Bundle Python services
.\BUILD_PYTHON_BUNDLES.ps1

# Build Electron app (all platforms)
.\BUILD_ELECTRON_APP.ps1

# Platform-specific builds
cd qumail-frontend
npm run electron:dist:win      # Windows
npm run electron:dist:mac      # macOS
npm run electron:dist:linux    # Linux
```

### Testing

```powershell
# Frontend tests
cd qumail-frontend
npm test

# Backend tests
cd qumail-backend
pytest

# Lint
cd qumail-frontend
npm run lint
```

## 🔧 Configuration

### Environment Variables

Create `.env` files:

**qumail-backend/.env**:
```env
BACKEND_PORT=8000
KME1_URL=http://localhost:8010
KME2_URL=http://localhost:8020
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

**qumail-frontend/.env**:
```env
VITE_API_URL=http://localhost:8000
VITE_APP_VERSION=1.0.0
```

### Customize Icons

Replace files in `qumail-frontend/build/`:
- `icon.ico` - Windows icon (256x256)
- `icon.icns` - macOS icon set
- `icon.png` - Linux icon (512x512)

See `qumail-frontend/build/README.md` for icon generation guide.

## 📚 Documentation

- **[Complete Guide](ELECTRON_APP_GUIDE.md)** - Detailed documentation
- **[API Reference](qumail-backend/README.md)** - Backend API docs
- **[Frontend Docs](qumail-frontend/README.md)** - Component docs
- **[Security Guide](.github/instructions/instructon1.instructions.md)** - Security requirements

## 🐛 Troubleshooting

### Backend Won't Start

```powershell
# Check Python
python --version

# Test backend manually
cd qumail-backend
python -m uvicorn app.main:app --port 8000

# Check logs in Electron DevTools
```

### Blank Window

```powershell
# Clear build artifacts
cd qumail-frontend
Remove-Item -Recurse dist, dist-electron

# Rebuild
npm run build
npm run electron:dev
```

### Build Fails

```powershell
# Reinstall dependencies
cd qumail-frontend
npm ci

cd ../qumail-backend
pip install -r requirements.txt --force-reinstall

# Try again
cd ..
.\BUILD_ELECTRON_APP.ps1
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- **Electron** - Cross-platform desktop framework
- **ETSI QKD 014** - Quantum key distribution standard
- **Next Door Key Simulator** - KME reference implementation
- **liboqs** - Post-quantum cryptography library

## 📧 Contact

- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Email**: support@qumail.example.com
- **Website**: https://qumail.example.com

## 🗺️ Roadmap

- [ ] Auto-update mechanism
- [ ] Multiple email account support
- [ ] Calendar integration
- [ ] Mobile companion app
- [ ] Hardware security key support
- [ ] Quantum RNG integration
- [ ] Enterprise deployment tools

---

**Made with ❤️ and quantum physics**
