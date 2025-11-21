# QuMail Secure Email - Installation & Startup Guide

> **Quantum-secured email system with KME integration**

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **PowerShell** (Windows) or compatible shell
- **Git** (for cloning)

### One-Command Installation
```powershell
# Install all dependencies for backend, KMS, next-door-key-simulator, and frontend
.\install_all_requirements.ps1
```

### One-Command System Start
```powershell
# Start complete system: KME1, KME2, Backend, Frontend
.\START_COMPLETE_SYSTEM.ps1
```

---

## 📦 Detailed Installation

### 1. Install System Dependencies

**Install Python 3.8+:**
- Windows: Download from [python.org](https://python.org) or use `winget install Python.Python.3.12`
- Make sure `python` and `pip` are in PATH

**Install Node.js 16+:**
- Windows: Download from [nodejs.org](https://nodejs.org) or use `winget install OpenJS.NodeJS`
- Make sure `node` and `npm` are in PATH

### 2. Install Project Dependencies

**Option A: System-wide installation (recommended for testing)**
```powershell
.\install_all_requirements.ps1
```

**Option B: Virtual environments (recommended for development)**
```powershell
.\install_all_requirements.ps1 -UseVenv
```

This installs dependencies for:
- ✅ **Backend** (`qumail-backend/requirements.txt`)
- ✅ **KMS** (`qumail-kms/requirements.txt`) 
- ✅ **Next-Door Key Simulator** (`next-door-key-simulator/requirements.txt`)
- ✅ **Frontend** (`qumail-frontend/package.json`)

### 3. Verify Installation
```powershell
# Check Python packages
python -c "import fastapi, uvicorn, cryptography; print('✅ Python deps OK')"

# Check Node packages
cd qumail-frontend
npm list --depth=0
cd ..
```

---

## 🎯 System Startup

### Complete System (Recommended)
```powershell
# Starts all services in correct order: KME1 → KME2 → Backend → Frontend
.\START_COMPLETE_SYSTEM.ps1
```

**What this does:**
1. **KME1** (port 8010) - Master key generator
2. **KME2** (port 8020) - Slave key retriever  
3. **Backend** (port 8000) - QuMail API server
4. **Frontend** (port 5173) - React UI

### Individual Service Startup

**Start KME Servers Only:**
```powershell
.\start_kme_servers.ps1
```

**Start Backend Only:**
```powershell
cd qumail-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Start Frontend Only:**
```powershell
cd qumail-frontend
npm run dev
```

**Start KMS Only:**
```powershell
cd qumail-kms
python main.py
```

---

## 🔧 Configuration

### Environment Files
- **Backend**: `qumail-backend/.env`
- **KMS**: `qumail-kms/.env.kms1`, `qumail-kms/.env.kms2`
- **Next-Door**: `next-door-key-simulator/.env.kme1`, `next-door-key-simulator/.env.kme2`

### Default Ports
| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000 |
| KME1 (Master) | 8010 | http://localhost:8010 |
| KME2 (Slave) | 8020 | http://localhost:8020 |
| KMS | 9000 | http://localhost:9000 |

---

## ✅ Verification & Testing

### 1. Check All Services Running
```powershell
# Quick health check
curl http://localhost:8000/health      # Backend
curl http://localhost:8010/api/v1/kme/status  # KME1
curl http://localhost:8020/api/v1/kme/status  # KME2
```

### 2. Test Quantum Key Generation
```powershell
python test_shared_pool.py
```

### 3. Test Complete Email Flow
```powershell
python test_complete_email_flow.py
```

### 4. Frontend Access
- Open browser: http://localhost:5173
- Sign in with Google OAuth
- Compose encrypted email
- Test all 4 security levels

---

## 🐛 Troubleshooting

### Common Issues

**1. "Python not found"**
```powershell
# Add Python to PATH or use full path
C:\Python312\python.exe -m pip install -r requirements.txt
```

**2. "npm not found"**  
```powershell
# Install Node.js or add to PATH
winget install OpenJS.NodeJS
```

**3. "Port already in use"**
```powershell
# Kill existing processes
.\KILL_KMS.ps1
# Or check what's using the port
netstat -ano | findstr :8000
```

**4. "Permission denied" on Windows**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**5. "Certificate errors"**
```powershell
# Regenerate certificates
cd next-door-key-simulator/certs
python generate_certs.py
```

### Service Logs

**Backend logs:**
```powershell
cd qumail-backend
tail -f qumail-backend.log
```

**KMS logs:**
```powershell  
cd qumail-kms
tail -f qumail-kms.log
```

**KME logs:** Check terminal output where started

---

## 🏗️ Development Setup

### Virtual Environment Setup
```powershell
# Backend
cd qumail-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# KMS  
cd ..\qumail-kms
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Next-Door
cd ..\next-door-key-simulator
python -m venv venv
venv\Scripts\activate  
pip install -r requirements.txt
```

### Development Commands
```powershell
# Backend with auto-reload
cd qumail-backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend with hot-reload
cd qumail-frontend
npm run dev

# KMS with debug logging
cd qumail-kms
python main.py --log-level DEBUG
```

---

## 📁 Project Structure

```
qumail-secure-email/
├── 📄 install_all_requirements.ps1     # Install all dependencies
├── 📄 START_COMPLETE_SYSTEM.ps1       # Start all services
├── 📄 INSTALLATION_AND_STARTUP.md     # This file
├── 🗂️ qumail-backend/                 # FastAPI backend
│   ├── requirements.txt
│   └── app/
├── 🗂️ qumail-frontend/                # React frontend  
│   ├── package.json
│   └── src/
├── 🗂️ qumail-kms/                     # Key Management Service
│   ├── requirements.txt
│   └── services/
├── 🗂️ next-door-key-simulator/        # ETSI QKD 014 simulator
│   ├── requirements.txt
│   └── server/
└── 🗂️ certs/                          # SSL certificates
```

---

## ☁️ Cloud Deployment (Render + MongoDB Atlas)

Use this section when you want to run every server component in the cloud while the Electron app stays local.

### 1. Provision Managed Services

1. **MongoDB Atlas (Free M0)**
  - Create a cluster + database user.
  - Allow Render egress IPs or temporarily `0.0.0.0/0`.
  - Copy the SRV URI (see `.env.template` for format).
  - Create collections: `users`, `drafts`, `encryption_metadata`.
2. **Redis Cloud (30 MB Free)**
  - Spin up an instance and copy the `redis://` URL with credentials.
  - This URL is shared by both KMEs and the backend for the key pool.

### 2. Render Deployment Steps

1. Commit `render.yaml` and push to GitHub.
2. In Render → **Blueprints**, create a new instance pointing to this repo/branch.
3. Render will detect three services (KME1, KME2, backend). Keep the free plan for each.
4. For every service, set the environment variables listed in `.env.template`:
  - **KMEs**: `PORT`, `KME_ID`, `REDIS_URL`, `SHARED_POOL_ENABLED=true`.
  - **Backend**: `DATABASE_URL`, `REDIS_URL`, `KME1_URL`, `KME2_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GMAIL_SCOPES`, `JWT_SECRET`.
5. Deploy and wait for green status. Capture the public URLs (e.g. `https://qumail-backend.onrender.com`).

### 3. Electron App Configuration

- Update `qumail-electron/config.production.js` (or environment variables) with:
  - `apiBaseUrl = https://qumail-backend.onrender.com/api/v1`
  - `oauthRedirect = qumail://auth/callback`
- Rebuild installers (`npm run build:<platform>`) to target the cloud backend.

### 4. Verification & Smoke Tests

Run the deployment verification script (see `scripts/check_render_deployment.py` added in this update):

```powershell
python scripts/check_render_deployment.py \`
  --backend https://qumail-backend.onrender.com \`
  --kme1 https://qumail-kme1.onrender.com \`
  --kme2 https://qumail-kme2.onrender.com \`
  --mongo "mongodb+srv://..." \`
  --redis "redis://..."
```

The script checks:
- KME `/health` endpoints
- Backend `/health`
- Quantum key generation/consumption via Redis
- MongoDB Atlas connectivity

If everything returns ✅, the Electron desktop app can now operate against the cloud stack.

---

## 🔐 Security Notes

- **Quantum Keys**: Generated using `os.urandom()` (cryptographically secure)
- **SSL/TLS**: Self-signed certificates for development (replace for production)
- **OAuth**: Google OAuth integration for Gmail access
- **Encryption Levels**: 
  - Level 1: OTP (One-Time Pad)
  - Level 2: AES-256-GCM + Quantum Keys
  - Level 3: Post-Quantum Cryptography (Kyber1024 + Dilithium5)
  - Level 4: RSA-4096 + AES Hybrid

---

## 📞 Support

### Quick Commands Reference
```powershell
# Full install and start
.\install_all_requirements.ps1
.\START_COMPLETE_SYSTEM.ps1

# Check system status  
.\CHECK_STATUS.ps1

# Kill all services
.\KILL_KMS.ps1

# Restart everything
.\NUCLEAR_RESTART.ps1
```

### Documentation Files
- `README.md` - Project overview
- `QKD_INTEGRATION_GUIDE.md` - Quantum key integration
- `SHARED_POOL_DOCUMENTATION_INDEX.md` - Key pool architecture
- `YOUR_REQUEST_DELIVERED.md` - Feature implementation status

---

## 🎉 Success Indicators

When everything is working correctly:

✅ **Frontend**: http://localhost:5173 loads QuMail interface  
✅ **Backend**: http://localhost:8000/docs shows FastAPI docs  
✅ **KME1**: http://localhost:8010/api/v1/kme/status returns KME info  
✅ **KME2**: http://localhost:8020/api/v1/kme/status returns KME info  
✅ **Encryption**: Can send emails with all 4 security levels  
✅ **Decryption**: Can decrypt received emails in QuMail  
✅ **Gmail**: Encrypted emails appear as gibberish in Gmail web  

**🚀 You're ready to use QuMail Secure Email!**