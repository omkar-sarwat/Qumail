# 🔐 QuMail - Quantum-Secure Email System

<div align="center">

![QuMail Logo](qumail-mobile/assets/qumail-logo.png)

**The World's First Quantum Key Distribution (QKD) Secured Email Platform**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![ETSI QKD 014](https://img.shields.io/badge/ETSI-QKD%20014-green.svg)](https://www.etsi.org)

[Features](#-features) • [Architecture](#-system-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Security](#-security-levels) • [API](#-api-documentation)

</div>

---

## 📖 Overview

QuMail is a cutting-edge secure email platform that leverages **Quantum Key Distribution (QKD)** technology to provide unprecedented levels of email security. Built following the **ETSI QKD 014 standard**, QuMail offers multiple encryption levels including quantum One-Time Pad (OTP), AES-256-GCM with quantum enhancement, and Post-Quantum Cryptography (PQC).

### 🎯 Problem Statement

Traditional email encryption relies on mathematical complexity that could be broken by future quantum computers. QuMail solves this by using:
- **Quantum keys** that are physically impossible to intercept without detection
- **Post-quantum algorithms** resistant to quantum computer attacks
- **Multiple fallback layers** ensuring security even without quantum hardware

---

## ✨ Features

### 🔒 Security Features
- **4 Encryption Levels** - From quantum OTP to hybrid RSA+AES
- **ETSI QKD 014 Compliant** - Industry standard quantum key management
- **End-to-End Encryption** - Messages encrypted before leaving your device
- **Zero-Knowledge Architecture** - Server never sees plaintext content

### 📧 Email Features
- **Gmail Integration** - Seamless OAuth2 authentication
- **Rich Text Editor** - Full formatting support with attachments
- **Offline Support** - Read and compose emails without internet
- **Cross-Platform** - Web, Desktop (Electron), and Mobile (React Native)

### 🎨 User Experience
- **Modern Dark UI** - Beautiful, eye-friendly interface
- **Real-time Sync** - Instant email updates
- **Smart Compose** - Auto-suggestions and templates
- **Security Indicators** - Visual encryption level badges

---

## 📸 Screenshots

### Login Screen
*Secure Google OAuth authentication with quantum branding*

![Login Screen](docs/screenshots/login.png)

### Main Dashboard
*Email inbox with encryption level indicators and quantum status*

![Dashboard](docs/screenshots/dashboard.png)

### Compose Email
*Rich text editor with security level selector*

![Compose Email](docs/screenshots/compose.png)

### Quantum Security Panel
*Real-time quantum key status and encryption details*

![Security Panel](docs/screenshots/security-panel.png)

### Email Decryption
*Secure decryption with authentication verification*

![Decryption](docs/screenshots/decrypt.png)

### Mobile App
*Native mobile experience for iOS and Android*

![Mobile App](docs/screenshots/mobile.png)

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           QuMail System Architecture                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │
│  │   Frontend  │     │   Backend   │     │  KME Servers │                │
│  │   (React)   │◄───►│  (FastAPI)  │◄───►│ (ETSI QKD)  │                │
│  └─────────────┘     └─────────────┘     └─────────────┘                │
│        │                    │                    │                        │
│        │                    │                    │                        │
│        ▼                    ▼                    ▼                        │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │
│  │  Electron   │     │  MongoDB    │     │   Quantum   │                │
│  │   Desktop   │     │  (Storage)  │     │   Keys Pool │                │
│  └─────────────┘     └─────────────┘     └─────────────┘                │
│        │                    │                                            │
│        │                    │                                            │
│        ▼                    ▼                                            │
│  ┌─────────────┐     ┌─────────────┐                                    │
│  │   Mobile    │     │ Gmail API   │                                    │
│  │ (React Nat) │     │ (OAuth2)    │                                    │
│  └─────────────┘     └─────────────┘                                    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React 18 + TypeScript + Vite | Web interface with TailwindCSS |
| **Desktop** | Electron 27 | Native desktop app with SQLite |
| **Mobile** | React Native + Expo | iOS and Android apps |
| **Backend** | FastAPI + Python 3.10+ | REST API and encryption services |
| **Database** | MongoDB Atlas | Cloud-hosted email and key storage |
| **KME Servers** | Python + ETSI QKD 014 | Quantum key management entities |

---

## 🔐 Security Levels

QuMail implements four distinct security levels:

### Level 1: Quantum One-Time Pad (OTP) 🟢
```
Security: UNCONDITIONAL (Information-theoretic security)
Key Source: QKD-generated quantum keys
Algorithm: XOR with true random key
Use Case: Maximum security communications
```

### Level 2: Quantum AES-256-GCM 🔵
```
Security: VERY HIGH (256-bit quantum-enhanced)
Key Source: HKDF with quantum entropy
Algorithm: AES-256-GCM authenticated encryption
Use Case: High-volume secure emails
```

### Level 3: Post-Quantum Cryptography (PQC) 🟣
```
Security: HIGH (Quantum-resistant)
Key Source: ML-KEM-1024 (Kyber) key encapsulation
Algorithm: ML-DSA-87 (Dilithium) + AES-256-GCM
Use Case: Future-proof encryption
```

### Level 4: Hybrid RSA + AES 🟡
```
Security: STANDARD (Legacy compatible)
Key Source: RSA-4096 key exchange
Algorithm: RSA-OAEP + AES-256-GCM
Use Case: Compatibility fallback
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **MongoDB** (local or Atlas)
- **Git**

### Quick Start

```bash
# Clone the repository
git clone https://github.com/omkarsarswat/Qumail_.git
cd Qumail_

# Setup backend
cd qumail-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials

# Setup frontend
cd ../qumail-frontend
npm install
cp .env.example .env
# Edit .env with your settings

# Start KME servers (in separate terminals)
cd ../next-door-key-simulator
pip install -r requirements.txt
python app.py  # KME1 on port 8010

# Start backend
cd ../qumail-backend
uvicorn app.main:app --reload --port 8000

# Start frontend
cd ../qumail-frontend
npm run dev
```

### Environment Configuration

Create `.env` files from the examples:

**Backend (`qumail-backend/.env`):**
```env
# Database
DATABASE_URL=mongodb+srv://user:password@cluster.mongodb.net/qumail

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/callback

# Security Keys (generate your own!)
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_MASTER_KEY=your-fernet-key

# KME Servers
KM1_BASE_URL=https://qumail-kme1-xujk.onrender.com
KM2_BASE_URL=https://qumail-kme2-c341.onrender.com
```

**Frontend (`qumail-frontend/.env`):**
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

---

## 📱 Usage

### Sending an Encrypted Email

1. **Login** with your Google account
2. Click **Compose** to create a new email
3. Select your desired **Security Level** (1-4)
4. Write your message and click **Send**
5. The email is encrypted before transmission

### Reading an Encrypted Email

1. Open an email from your inbox
2. Click **Decrypt** button
3. Authenticate if required (for high-security levels)
4. View the decrypted content

### Checking Quantum Key Status

1. Navigate to **Settings > Quantum Security**
2. View available quantum keys
3. Monitor key consumption and generation

---

## 🌐 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/google` | Start OAuth flow |
| POST | `/api/v1/auth/callback` | Handle OAuth callback |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout user |

### Email Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/emails/inbox` | Get inbox emails |
| GET | `/api/v1/emails/{id}` | Get single email |
| POST | `/api/v1/emails/send/quantum` | Send encrypted email |
| POST | `/api/v1/emails/{id}/decrypt` | Decrypt email |

### Quantum Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quantum/status` | Get quantum system status |
| GET | `/api/v1/quantum/keys/available` | Check key availability |
| POST | `/api/v1/encryption/encrypt` | Encrypt content |
| POST | `/api/v1/encryption/decrypt` | Decrypt content |

Full API documentation available at: `http://localhost:8000/docs`

---

## 🧪 Testing

```bash
# Run backend tests
cd qumail-backend
pytest tests/ -v

# Run encryption level tests
python -m pytest tests/test_optimized_km_all_levels.py -v

# Test KME connections
python quick_check_kme.py

# Run frontend tests
cd qumail-frontend
npm test
```

---

## 📂 Project Structure

```
Qumail_/
├── qumail-backend/          # FastAPI backend server
│   ├── app/
│   │   ├── api/             # API route handlers
│   │   ├── services/        # Business logic
│   │   │   ├── encryption/  # Encryption implementations
│   │   │   └── ...
│   │   ├── models/          # Database models
│   │   └── config.py        # Configuration
│   ├── tests/               # Backend tests
│   └── requirements.txt
│
├── qumail-frontend/         # React frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── services/        # API services
│   │   ├── stores/          # State management
│   │   └── ...
│   ├── electron/            # Electron desktop app
│   └── package.json
│
├── qumail-mobile/           # React Native mobile app
│   ├── app/                 # App screens
│   └── components/          # Mobile components
│
├── next-door-key-simulator/ # ETSI QKD KME servers
│   ├── app.py               # KME server
│   ├── server/              # Server implementation
│   └── router/              # API routes
│
└── docs/                    # Documentation
    └── screenshots/         # Application screenshots
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint/Prettier for TypeScript
- Write tests for new features
- Update documentation as needed

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ETSI QKD Industry Specification Group** - For the QKD 014 standard
- **NIST** - For post-quantum cryptography standards
- **Open Quantum Safe (liboqs)** - For PQC implementations
- **Google** - For Gmail API and OAuth services

---

## 📞 Contact

**Team CryptoNova** - Smart India Hackathon 2025

- **Project Lead**: Omkar Sarswat
- **GitHub**: [@omkarsarswat](https://github.com/omkarsarswat)
- **Email**: sarswatomkar9421@gmail.com

---

<div align="center">

**Built with ❤️ for a quantum-secure future**

⭐ Star this repository if you find it useful!

</div>
