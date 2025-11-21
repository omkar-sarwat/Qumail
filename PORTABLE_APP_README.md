# QuMail Secure Email - Portable Application Guide

## 🎉 Your Application is Ready!

The QuMail Secure Email application has been successfully built as a portable executable.

## 📍 Location

```
qumail-secure-email/qumail-frontend/release/QuMail-Portable/QuMail.exe
```

## 🚀 Quick Start (Easiest Way)

Simply run the launcher script from the root directory:

```powershell
.\LAUNCH_QUMAIL_APP.ps1
```

This will:
- ✅ Start KME Server 1 (Port 8010)
- ✅ Start KME Server 2 (Port 8020)  
- ✅ Start Backend Server (Port 8000)
- ✅ Launch the QuMail desktop application

## 🔧 Manual Start (If Needed)

If you prefer to start services manually:

### Step 1: Start KME Servers

```powershell
# Terminal 1 - KME Server 1
cd next-door-key-simulator
python app.py --port 8010 --cert-path ./certs/kme-1-local-zone --mode kme1

# Terminal 2 - KME Server 2
cd next-door-key-simulator
python app.py --port 8020 --cert-path ./certs/kme-2-local-zone --mode kme2
```

### Step 2: Start Backend

```powershell
# Terminal 3 - Backend
cd qumail-backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Launch Application

```powershell
cd qumail-frontend\release\QuMail-Portable
.\QuMail.exe
```

## 📦 Distribution

To share the application with others:

1. **Copy the entire `QuMail-Portable` folder** to any location
2. Make sure the recipient has the backend and KME servers running
3. Double-click `QuMail.exe` to run

## 🔐 Features

- ✅ **4 Security Levels**: OTP, AES-256-GCM, Post-Quantum (Kyber+Dilithium), RSA-4096
- ✅ **Quantum Key Distribution**: Real quantum keys from KME servers
- ✅ **End-to-End Encryption**: Messages encrypted before sending to Gmail
- ✅ **Gmail Integration**: OAuth2 authentication with Google
- ✅ **Offline Capable**: Desktop app with local encryption
- ✅ **Cross-Platform**: Windows executable (portable, no installation required)

## 🌐 API Endpoints

Once running, the following services will be available:

- **Backend API**: http://localhost:8000
- **Backend Docs**: http://localhost:8000/docs
- **KME Server 1**: http://localhost:8010
- **KME Server 2**: http://localhost:8020

## 🔄 Rebuilding the App

If you make changes to the code, rebuild using:

```powershell
.\PACKAGE_ELECTRON_MANUALLY.ps1
```

## ⚙️ System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB free space
- **Python**: 3.8+ (for backend/KME servers)
- **Node.js**: 18+ (only needed for rebuilding)

## 🐛 Troubleshooting

### App won't start
- Check that all backend services are running (ports 8000, 8010, 8020)
- Run `.\LAUNCH_QUMAIL_APP.ps1` to start everything automatically

### "Failed to connect to backend"
- Verify backend is running on port 8000
- Check Windows Firewall isn't blocking connections

### Encryption errors
- Ensure both KME servers (8010, 8020) are running
- Check the backend terminal for detailed error logs

## 📝 Notes

- This is a **portable version** - no installation required
- The app requires the backend and KME servers to be running
- All data is stored locally (MongoDB) - not in the cloud
- Gmail integration requires OAuth2 authentication on first use

## 🎯 Next Steps

1. Run `.\LAUNCH_QUMAIL_APP.ps1`
2. Wait for all services to start (10-15 seconds)
3. The QuMail app will open automatically
4. Sign in with your Google account
5. Start sending quantum-encrypted emails!

---

**Built with ❤️ using Electron, React, Python FastAPI, and Quantum Key Distribution**
