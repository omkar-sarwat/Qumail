# Security Configuration Guide

This document provides instructions on setting up credentials and sensitive configuration for QuMail.

## Required Credentials

### 1. Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API and Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure the consent screen
6. Set application type to "Web application"
7. Add authorized redirect URIs:
   - `http://localhost:5173/auth/callback` (development)
   - `http://localhost:5174/auth/callback` (alternative dev port)
   - Your production URL callback
8. Copy the Client ID and Client Secret

### 2. MongoDB Database

#### Option A: MongoDB Atlas (Recommended for production)
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a cluster
3. Create a database user
4. Get your connection string (mongodb+srv://...)
5. Whitelist your IP address

#### Option B: Local MongoDB (Development)
```bash
# Install MongoDB locally or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. QKD Key Management Servers (KME)

The KME servers simulate quantum key distribution for secure encryption.

1. Generate certificates using the provided scripts in `next-door-key-simulator/certs/`
2. Configure KME server URLs in your `.env` file
3. Set up SAE (Secure Application Entity) IDs

## Environment Setup

### Backend (.env)

Copy `qumail-backend/.env.example` to `qumail-backend/.env` and fill in:

```env
# Security Keys (generate your own!)
SECRET_KEY=<generate-with-openssl-rand-base64-32>
ENCRYPTION_MASTER_KEY=<generate-fernet-key>

# Database
DATABASE_URL=<your-mongodb-connection-string>

# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/callback
```

### Frontend (.env)

Copy `qumail-frontend/.env.example` to `qumail-frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
```

### Google Client Secrets

Copy `qumail-backend/client_secrets.example.json` to `qumail-backend/client_secrets.json` and fill in your credentials.

## Generating Security Keys

### Secret Key
```bash
openssl rand -base64 32
```

### Fernet Encryption Key
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Certificate Generation

For local development, generate test certificates:

```bash
cd next-door-key-simulator/certs
./generate.sh  # or run the commands manually
```

## Security Best Practices

1. **Never commit** `.env` files or `client_secrets.json`
2. **Rotate secrets** regularly in production
3. **Use environment variables** in production deployments
4. **Enable HTTPS** in production
5. **Review OAuth scopes** - only request what you need

## Files That Should NEVER Be Committed

- `.env` (any environment)
- `client_secrets.json`
- `*.key` (private keys)
- `*.pem` (certificates with private keys)
- `*.pfx` / `*.p12` (certificate packages)
- Database dumps
- Log files with sensitive data

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly by emailing the maintainers directly. Do not open public issues for security vulnerabilities.
