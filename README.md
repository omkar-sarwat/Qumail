<div align="center">

# QuMail

### Quantum-Secure Email Communication Platform

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://mongodb.com)
[![ETSI QKD 014](https://img.shields.io/badge/ETSI-QKD%20014-FF6B35)](https://www.etsi.org)

**Enterprise-grade email encryption powered by Quantum Key Distribution (QKD) technology**

[Live Demo](https://qumail-frontend.onrender.com) · [API Docs](https://qumail-backend-8ttg.onrender.com/docs) · [Report Bug](https://github.com/omkarsarswat/Qumail_/issues)

---

</div>

## About The Project

QuMail addresses a critical vulnerability in modern digital communication: **traditional encryption algorithms will become obsolete** once large-scale quantum computers become available. This platform implements a complete quantum-secure email system that protects communications today and into the post-quantum era.

Built as a comprehensive full-stack solution, QuMail demonstrates proficiency in:

- **Cryptographic Engineering** — Implementation of ETSI QKD 014 standard, post-quantum algorithms (ML-KEM/Kyber, ML-DSA/Dilithium), and classical encryption
- **Distributed Systems** — Multi-server architecture with quantum key management entities (KMEs)
- **Full-Stack Development** — React/TypeScript frontend, FastAPI backend, React Native mobile
- **Cloud Infrastructure** — Production deployment on Render with MongoDB Atlas

<br/>

## Key Features

<table>
<tr>
<td width="50%">

### 🔐 Security Architecture

- **4-Tier Encryption System**
  - Level 1: Quantum One-Time Pad (OTP) — *Information-theoretic security*
  - Level 2: Quantum-Enhanced AES-256-GCM
  - Level 3: Post-Quantum Cryptography (ML-KEM-1024 + ML-DSA-87)
  - Level 4: Hybrid RSA-4096 + AES-256
- **ETSI QKD 014 Compliance**
- **Zero-Knowledge Architecture**
- **End-to-End Encryption**

</td>
<td width="50%">

### ⚡ Technical Highlights

- **Real-time Key Management** with dual KME servers
- **OAuth 2.0 Integration** with Gmail API
- **Two-Factor Authentication** (TOTP)
- **Cross-Platform Support** — Web, Desktop (Electron), Mobile (React Native)
- **RESTful API** with OpenAPI 3.0 documentation
- **Automated CI/CD** pipeline

</td>
</tr>
</table>

<br/>

## System Architecture

```
                                    ┌──────────────────────────────────────┐
                                    │           QUMAIL ARCHITECTURE        │
                                    └──────────────────────────────────────┘

    ┌─────────────────┐                    ┌─────────────────┐                    ┌─────────────────┐
    │                 │                    │                 │                    │                 │
    │   Web Client    │◄──────────────────►│   FastAPI       │◄──────────────────►│   MongoDB       │
    │   React + TS    │        REST        │   Backend       │      Mongoose      │   Atlas         │
    │   TailwindCSS   │                    │   Python 3.10+  │                    │                 │
    │                 │                    │                 │                    │                 │
    └─────────────────┘                    └────────┬────────┘                    └─────────────────┘
                                                    │
    ┌─────────────────┐                             │                             ┌─────────────────┐
    │                 │                             │                             │                 │
    │   Desktop App   │                             │           ETSI QKD 014      │   Gmail API     │
    │   Electron      │                             │                             │   OAuth 2.0     │
    │                 │                             │                             │                 │
    └─────────────────┘                    ┌────────▼────────┐                    └─────────────────┘
                                           │                 │
    ┌─────────────────┐                    │   Encryption    │
    │                 │                    │   Service       │
    │   Mobile App    │                    │                 │
    │   React Native  │                    │   • OTP         │
    │   Expo          │                    │   • AES-256-GCM │
    │                 │                    │   • ML-KEM/DSA  │
    └─────────────────┘                    │   • RSA-4096    │
                                           │                 │
                                           └────────┬────────┘
                                                    │
                            ┌───────────────────────┴───────────────────────┐
                            │                                               │
                   ┌────────▼────────┐                             ┌────────▼────────┐
                   │                 │                             │                 │
                   │   KME Server 1  │◄───────────────────────────►│   KME Server 2  │
                   │   (Key Gen)     │      Quantum Channel        │   (Key Recv)    │
                   │   Port 8010     │                             │   Port 8020     │
                   │                 │                             │                 │
                   └─────────────────┘                             └─────────────────┘
```

<br/>

## Technology Stack

| Layer | Technologies |
|:------|:-------------|
| **Frontend** | React 18, TypeScript 5, Vite, TailwindCSS, Zustand, React Query |
| **Desktop** | Electron 27, SQLite (offline storage) |
| **Mobile** | React Native, Expo, AsyncStorage |
| **Backend** | Python 3.10+, FastAPI, Pydantic V2, Motor (async MongoDB) |
| **Database** | MongoDB Atlas, Redis (caching) |
| **Security** | liboqs (PQC), cryptography, PyOTP, python-jose |
| **Infrastructure** | Render, Docker, GitHub Actions |
| **APIs** | Gmail API, Google OAuth 2.0, ETSI QKD 014 |

<br/>

## Security Implementation

### Encryption Levels Explained

| Level | Algorithm | Key Source | Security Model | Use Case |
|:-----:|:----------|:-----------|:---------------|:---------|
| **1** | One-Time Pad (XOR) | QKD Quantum Keys | Information-theoretic | Maximum security, limited by key availability |
| **2** | AES-256-GCM | HKDF + Quantum Entropy | Computational (256-bit) | High-volume secure communications |
| **3** | ML-KEM-1024 + ML-DSA-87 | Post-Quantum KEM | Quantum-resistant | Future-proof encryption |
| **4** | RSA-4096 + AES-256 | Asymmetric Exchange | Computational | Backwards compatibility |

### ETSI QKD 014 Standard

The Key Management Entity (KME) servers implement the ETSI GS QKD 014 V1.1.1 standard:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETSI QKD 014 API Endpoints                   │
├─────────────────────────────────────────────────────────────────┤
│  GET  /api/v1/keys/{slave_SAE_ID}/status    → Key availability  │
│  POST /api/v1/keys/{slave_SAE_ID}/enc_keys  → Request keys      │
│  POST /api/v1/keys/{master_SAE_ID}/dec_keys → Retrieve keys     │
└─────────────────────────────────────────────────────────────────┘
```

<br/>

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- MongoDB Atlas account (or local MongoDB)
- Google Cloud Console project (for OAuth)

### Installation

```bash
# Clone the repository
git clone https://github.com/omkarsarswat/Qumail_.git
cd Qumail_

# Backend setup
cd qumail-backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure environment variables

# Frontend setup
cd ../qumail-frontend
npm install
cp .env.example .env      # Configure environment variables

# Start development servers
# Terminal 1: Backend
cd qumail-backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd qumail-frontend && npm run dev
```

### Environment Variables

<details>
<summary><b>Backend Configuration</b></summary>

```env
# Database
MONGODB_URL=mongodb+srv://<user>:<password>@cluster.mongodb.net/qumail

# Authentication
SECRET_KEY=<your-256-bit-secret>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>

# Quantum Key Management
KME1_BASE_URL=https://qumail-kme1-xujk.onrender.com
KME2_BASE_URL=https://qumail-kme2-c341.onrender.com
```

</details>

<details>
<summary><b>Frontend Configuration</b></summary>

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=<your-google-client-id>
```

</details>

<br/>

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `POST` | `/api/v1/auth/google` | Initiate Google OAuth flow |
| `GET` | `/api/v1/emails/inbox` | Fetch encrypted inbox |
| `POST` | `/api/v1/emails/send/quantum` | Send quantum-encrypted email |
| `POST` | `/api/v1/emails/{id}/decrypt` | Decrypt email content |
| `GET` | `/api/v1/quantum/status` | KME server status |
| `POST` | `/api/v1/encryption/encrypt` | Encrypt arbitrary content |

Full API documentation: **[Swagger UI](https://qumail-backend-8ttg.onrender.com/docs)**

<br/>

## Project Structure

```
QuMail/
├── qumail-backend/                 # FastAPI Backend Service
│   ├── app/
│   │   ├── api/                    # Route handlers
│   │   │   ├── auth.py             # OAuth & JWT authentication
│   │   │   ├── emails.py           # Email CRUD operations
│   │   │   └── encryption.py       # Encryption endpoints
│   │   ├── services/
│   │   │   ├── encryption/         # Encryption implementations
│   │   │   │   ├── level1_otp.py   # Quantum OTP
│   │   │   │   ├── level2_aes.py   # Quantum AES-256
│   │   │   │   ├── level3_pqc.py   # Post-quantum crypto
│   │   │   │   └── level4_rsa.py   # Hybrid RSA
│   │   │   └── optimized_km_client.py  # ETSI QKD client
│   │   ├── models/                 # Pydantic schemas
│   │   └── config.py               # Configuration management
│   ├── tests/                      # Pytest test suite
│   └── requirements.txt
│
├── qumail-frontend/                # React Web Application
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   ├── pages/                  # Route pages
│   │   ├── services/               # API client services
│   │   ├── stores/                 # Zustand state management
│   │   └── types/                  # TypeScript definitions
│   └── electron/                   # Electron desktop wrapper
│
├── qumail-mobile/                  # React Native Mobile App
│   ├── app/                        # Expo Router screens
│   └── components/                 # Mobile components
│
└── next-door-key-simulator/        # ETSI QKD 014 KME Servers
    ├── server/                     # KME server implementation
    └── router/                     # API route handlers
```

<br/>

## Testing

```bash
# Backend unit tests
cd qumail-backend
pytest tests/ -v --cov=app

# Encryption level integration tests
pytest tests/test_optimized_km_all_levels.py -v

# Frontend tests
cd qumail-frontend
npm run test
```

<br/>

## Deployment

The application is deployed on Render with the following services:

| Service | URL | Type |
|:--------|:----|:-----|
| Frontend | `qumail-frontend.onrender.com` | Static Site |
| Backend | `qumail-backend-8ttg.onrender.com` | Web Service |
| KME Server 1 | `qumail-kme1-xujk.onrender.com` | Web Service |
| KME Server 2 | `qumail-kme2-c341.onrender.com` | Web Service |

<br/>

## Performance Metrics

| Operation | Average Latency | Throughput |
|:----------|:---------------:|:----------:|
| Level 1 Encryption (1KB) | ~15ms | 66 ops/sec |
| Level 2 Encryption (1KB) | ~8ms | 125 ops/sec |
| Level 3 Encryption (1KB) | ~25ms | 40 ops/sec |
| Level 4 Encryption (1KB) | ~12ms | 83 ops/sec |
| Key Generation (QKD) | ~50ms | 20 keys/sec |

<br/>

## Roadmap

- [x] Core encryption service with 4 security levels
- [x] Gmail API integration with OAuth 2.0
- [x] ETSI QKD 014 compliant KME servers
- [x] Web application with React + TypeScript
- [x] Desktop application with Electron
- [x] Mobile application with React Native
- [ ] Hardware Security Module (HSM) integration
- [ ] Multi-tenant enterprise support
- [ ] Compliance certifications (SOC 2, HIPAA)

<br/>

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/enhancement`)
3. Commit changes (`git commit -m 'Add enhancement'`)
4. Push to branch (`git push origin feature/enhancement`)
5. Open a Pull Request

<br/>

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

<br/>

## Acknowledgments

- **ETSI QKD Industry Specification Group** — QKD 014 standard specification
- **NIST** — Post-quantum cryptography standardization (FIPS 203, 204)
- **Open Quantum Safe (liboqs)** — PQC library implementation
- **Google** — OAuth 2.0 and Gmail API

<br/>

---

<div align="center">

**Built by Omkar Sarswat**

[![GitHub](https://img.shields.io/badge/GitHub-omkarsarswat-181717?logo=github)](https://github.com/omkarsarswat)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin)](https://linkedin.com/in/omkarsarswat)
[![Email](https://img.shields.io/badge/Email-Contact-EA4335?logo=gmail)](mailto:sarswatomkar9421@gmail.com)

⭐ Star this repository if you find it useful

</div>
