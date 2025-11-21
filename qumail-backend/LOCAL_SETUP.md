# QuMail Backend - Local Development Setup (No Docker)

This guide provides step-by-step instructions for setting up the QuMail secure email backend on Windows without using Docker.

## 🚀 Quick Setup Guide

### 1. Prerequisites

Before starting, ensure you have the following installed on your Windows system:

#### Required Software
- **Python 3.11+** - [Download from python.org](https://python.org/downloads/)
  - ✅ Make sure to check "Add Python to PATH" during installation
- **Git** - [Download from git-scm.com](https://git-scm.com/download/win)
- **Visual Studio Code** (recommended) - [Download from code.visualstudio.com](https://code.visualstudio.com/)

#### Optional (for production)
- **PostgreSQL** - [Download from postgresql.org](https://www.postgresql.org/download/windows/)
  - Only needed if you want to use PostgreSQL instead of SQLite

### 2. Clone and Setup

```powershell
# Clone the repository (if not already done)
git clone <repository-url>
cd qumail-secure-email\qumail-backend

# Verify Python installation
python --version
# Should show Python 3.11.x or higher
```

### 3. Quick Start (Automated)

We've created startup scripts for easy setup:

#### Option A: PowerShell Script (Recommended)
```powershell
# Run the PowerShell startup script
.\start.ps1
```

#### Option B: Batch File
```cmd
# Run the batch file
start.bat
```

The startup scripts will automatically:
- ✅ Create a Python virtual environment
- ✅ Install all required dependencies
- ✅ Copy environment configuration template
- ✅ Validate your configuration
- ✅ Initialize the database
- ✅ Start the backend server

### 4. Manual Setup (If needed)

If you prefer manual setup or the scripts don't work:

```powershell
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# 2. Upgrade pip
python -m pip install --upgrade pip

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment configuration
copy .env.example .env

# 5. Configure .env file (see Configuration section below)
notepad .env

# 6. Initialize database
alembic upgrade head

# 7. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ Configuration

### Environment Configuration

1. **Copy the template**:
   ```powershell
   copy .env.example .env
   ```

2. **Edit the .env file** with your settings:

#### Basic Configuration
```bash
# Application settings
APP_ENV=development
DEBUG=true

# Security keys (IMPORTANT: Change these!)
SECRET_KEY=your-super-secret-key-here-minimum-32-characters
ENCRYPTION_MASTER_KEY=your-fernet-encryption-key-here
```

To generate secure keys:
```powershell
# Generate secret key
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_MASTER_KEY=' + Fernet.generate_key().decode())"
```

#### Database Configuration
The default configuration uses SQLite for easy local development:
```bash
# SQLite (default - no additional setup required)
DATABASE_URL=sqlite+aiosqlite:///./qumail.db
```

If you prefer PostgreSQL:
```bash
# PostgreSQL (requires local PostgreSQL installation)
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/qumail
```

#### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:3000/auth/callback`
6. Update your .env file:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
```

#### KM Server Configuration
Ensure your qkd_kme_server-master is running, then configure:
```bash
# KM server URLs
KM1_BASE_URL=https://localhost:13000
KM2_BASE_URL=https://localhost:14000

# Certificate paths (relative to backend directory)
KM1_CLIENT_CERT_PFX=../qkd_kme_server-master/certs/kme-1-local-zone/client_1.pfx
KM2_CLIENT_CERT_PFX=../qkd_kme_server-master/certs/kme-2-local-zone/client_3.pfx
KM1_CA_CERT=../qkd_kme_server-master/certs/kme-1-local-zone/ca.crt
KM2_CA_CERT=../qkd_kme_server-master/certs/kme-2-local-zone/ca.crt

# SAE IDs
SENDER_SAE_ID=1
RECEIVER_SAE_ID=3
```

## 🔍 Validation and Testing

### Configuration Validation
```powershell
# Validate your configuration
python validate_backend.py
```

This will check:
- ✅ Environment variables
- ✅ Certificate files
- ✅ Database connectivity
- ✅ KM server connectivity
- ✅ Google OAuth configuration
- ✅ Python dependencies

### Test the Backend

1. **Start the backend**:
   ```powershell
   .\start.ps1
   ```

2. **Access the API documentation**:
   - Open: http://localhost:8000/docs
   - Interactive API documentation

3. **Health check**:
   ```powershell
   curl http://localhost:8000/health
   ```

4. **Test encryption endpoint**:
   ```powershell
   curl -X POST "http://localhost:8000/api/v1/encryption/encrypt" `
     -H "Content-Type: application/json" `
     -d '{"content": "Test message", "security_level": "LEVEL_1", "user_email": "test@example.com"}'
   ```

## 🗄️ Database Options

### SQLite (Default - Recommended for Development)
- ✅ No additional setup required
- ✅ Database file created automatically
- ✅ Perfect for development and testing
- ❌ Single-user only

**Configuration**: Already set as default in .env.example

### PostgreSQL (Production Option)
- ✅ Multi-user support
- ✅ Better performance
- ✅ Production-ready
- ❌ Requires installation and setup

**Setup PostgreSQL** (if needed):
1. Download and install PostgreSQL
2. Create database and user:
   ```sql
   CREATE DATABASE qumail;
   CREATE USER qumail_user WITH ENCRYPTED PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE qumail TO qumail_user;
   ```
3. Update .env:
   ```bash
   DATABASE_URL=postgresql+asyncpg://qumail_user:your_password@localhost:5432/qumail
   ```

## 🔧 Development Workflow

### Starting Development
```powershell
# Activate virtual environment
venv\Scripts\Activate.ps1

# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Changes
- The server auto-reloads when you save Python files
- Database changes require migration:
  ```powershell
  alembic revision --autogenerate -m "Description of changes"
  alembic upgrade head
  ```

### Testing
```powershell
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 🐛 Common Issues and Solutions

### Issue: Python not found
**Error**: `'python' is not recognized as an internal or external command`

**Solution**: 
1. Reinstall Python and check "Add Python to PATH"
2. Or use full path: `C:\Python311\python.exe`

### Issue: Permission denied on scripts
**Error**: `execution of scripts is disabled on this system`

**Solution**: 
```powershell
# Enable script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: KM servers not reachable
**Error**: `KM server not reachable`

**Solutions**:
1. Ensure qkd_kme_server-master is running:
   ```powershell
   # Check if servers are running
   curl -k https://localhost:13000/health
   curl -k https://localhost:14000/health
   ```
2. Verify certificate paths in .env
3. Check Windows Firewall settings

### Issue: Database errors
**Error**: `Database connection failed`

**Solutions**:
- For SQLite: Check file permissions in the directory
- For PostgreSQL: Verify service is running and credentials are correct

### Issue: Import errors
**Error**: `ModuleNotFoundError`

**Solutions**:
1. Ensure virtual environment is activated
2. Reinstall dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## 📊 Monitoring and Logs

### Application Logs
- Log file: `qumail-backend.log`
- Console output when running with `--reload`

### View logs:
```powershell
# View recent logs
Get-Content qumail-backend.log -Tail 50

# Follow logs in real-time
Get-Content qumail-backend.log -Wait
```

### Health Monitoring
- Health endpoint: http://localhost:8000/health
- Status endpoint: http://localhost:8000/status
- Metrics endpoint: http://localhost:8000/metrics

## 🚀 Production Deployment

For production deployment on Windows:

1. **Use PostgreSQL** instead of SQLite
2. **Set production environment**:
   ```bash
   APP_ENV=production
   DEBUG=false
   ```
3. **Use a proper WSGI server**:
   ```powershell
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
4. **Set up Windows Service** (optional):
   - Use NSSM or similar to run as Windows service
5. **Configure reverse proxy** (IIS/nginx)
6. **Set up SSL certificates**

## 📚 Next Steps

1. **Frontend Development**: Create React+Electron app to use this backend
2. **Testing**: Run comprehensive tests with real KM servers
3. **Documentation**: Review API docs at `/docs`
4. **Security Review**: Validate all security configurations

## 🆘 Getting Help

### Quick Diagnostics
```powershell
# 1. Validate everything
python validate_backend.py

# 2. Check Python environment
python -c "import sys; print(sys.executable)"

# 3. Test individual components
python -c "from app.core.km_client import km1_client; print('KM client loaded')"

# 4. Check database
python -c "from app.database import engine; print('Database engine loaded')"
```

### Common Commands
```powershell
# Restart with fresh environment
deactivate  # if virtual env is active
Remove-Item venv -Recurse -Force
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Reset database
Remove-Item qumail.db  # SQLite only
alembic upgrade head

# Update dependencies
pip install --upgrade -r requirements.txt
```

---

## ✅ Success Indicators

You know everything is working when:
- ✅ `python validate_backend.py` shows all checks passed
- ✅ Backend starts without errors
- ✅ http://localhost:8000/health returns 200 OK
- ✅ http://localhost:8000/docs shows API documentation
- ✅ KM servers are reachable and responding
- ✅ Database operations work correctly

**Happy Coding! 🚀**

Your QuMail secure email backend is now ready for local development without Docker!