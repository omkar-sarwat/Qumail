#!/bin/bash

# QuMail Secure Email Backend Startup Script
# This script starts the QuMail backend with proper security configurations

set -e

echo "🔐 Starting QuMail Secure Email Backend..."

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  WARNING: Running as root is not recommended for security reasons"
    echo "   Consider creating a dedicated user for QuMail"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found"
    echo "   Please copy .env.example to .env and configure your settings"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ ERROR: No virtual environment found"
    exit 1
fi

echo "🐍 Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check for required KM server certificates
echo "🔑 Checking KM server certificates..."

# Source environment variables
set -a
source .env
set +a

# Check KM1 certificate
if [ ! -f "$KM1_CLIENT_CERT_PFX" ]; then
    echo "❌ ERROR: KM1 client certificate not found at: $KM1_CLIENT_CERT_PFX"
    echo "   Please ensure the qkd_kme_server-master is properly set up"
    exit 1
fi

if [ ! -f "$KM1_CA_CERT" ]; then
    echo "❌ ERROR: KM1 CA certificate not found at: $KM1_CA_CERT"
    exit 1
fi

# Check KM2 certificate
if [ ! -f "$KM2_CLIENT_CERT_PFX" ]; then
    echo "❌ ERROR: KM2 client certificate not found at: $KM2_CLIENT_CERT_PFX"
    echo "   Please ensure the qkd_kme_server-master is properly set up"
    exit 1
fi

if [ ! -f "$KM2_CA_CERT" ]; then
    echo "❌ ERROR: KM2 CA certificate not found at: $KM2_CA_CERT"
    exit 1
fi

echo "✅ All KM server certificates found"

# Check database configuration
echo "🗄️  Checking database configuration..."

if [[ "$DATABASE_URL" == *"sqlite"* ]]; then
    echo "📝 Using SQLite database (development mode)"
elif [[ "$DATABASE_URL" == *"postgresql"* ]]; then
    echo "🐘 Using PostgreSQL database (production ready)"
    
    # Test PostgreSQL connection
    echo "🔍 Testing PostgreSQL connection..."
    python3 -c "
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

async def test_db():
    try:
        url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(url)
        await conn.close()
        print('✅ PostgreSQL connection successful')
    except Exception as e:
        print(f'❌ PostgreSQL connection failed: {e}')
        exit(1)

asyncio.run(test_db())
" || {
    echo "❌ Database connection failed. Please check your DATABASE_URL"
    exit 1
}
else
    echo "❌ ERROR: Unsupported database URL format"
    exit 1
fi

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head || {
    echo "❌ Database migration failed"
    exit 1
}

echo "✅ Database migrations completed"

# Check Google OAuth configuration
echo "🔍 Checking Google OAuth configuration..."

if [ -z "$GOOGLE_CLIENT_ID" ] || [ "$GOOGLE_CLIENT_ID" = "your-google-oauth-client-id.apps.googleusercontent.com" ]; then
    echo "⚠️  WARNING: Google OAuth Client ID not configured"
    echo "   Gmail integration will not work until configured"
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ] || [ "$GOOGLE_CLIENT_SECRET" = "your-google-client-secret" ]; then
    echo "⚠️  WARNING: Google OAuth Client Secret not configured"
    echo "   Gmail integration will not work until configured"
fi

# Check encryption keys
echo "🔐 Checking encryption configuration..."

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-super-secret-key-here-change-this-in-production-min-32-chars" ]; then
    echo "❌ ERROR: SECRET_KEY not configured or using default value"
    echo "   Please generate a secure secret key and update .env"
    exit 1
fi

if [ -z "$ENCRYPTION_MASTER_KEY" ] || [ "$ENCRYPTION_MASTER_KEY" = "your-fernet-encryption-key-here-base64-encoded-32-bytes" ]; then
    echo "❌ ERROR: ENCRYPTION_MASTER_KEY not configured or using default value"
    echo "   Please generate a Fernet key and update .env"
    echo "   You can generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    exit 1
fi

echo "✅ Encryption configuration validated"

# Security checks
echo "🛡️  Running security checks..."

# Check for development vs production settings
if [ "$APP_ENV" = "production" ]; then
    echo "🚀 Production mode detected"
    
    if [ "$DEBUG" = "true" ]; then
        echo "⚠️  WARNING: DEBUG is enabled in production mode"
    fi
    
    if [ "$SHOW_DOCS" = "true" ]; then
        echo "⚠️  WARNING: API documentation is exposed in production mode"
    fi
    
    if [[ "$DATABASE_URL" == *"sqlite"* ]]; then
        echo "⚠️  WARNING: Using SQLite in production is not recommended"
    fi
else
    echo "🔧 Development mode detected"
fi

# Test KM server connectivity (optional - servers might not be running yet)
echo "🔍 Testing KM server connectivity (optional)..."

python3 -c "
import asyncio
import ssl
import aiohttp
import os

async def test_km_servers():
    km1_url = os.getenv('KM1_BASE_URL')
    km2_url = os.getenv('KM2_BASE_URL')
    
    # Create SSL context that ignores certificate errors for testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    for name, url in [('KM1', km1_url), ('KM2', km2_url)]:
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f'{url}/api/v1/keys/status', ssl=ssl_context) as response:
                    if response.status in [200, 401, 403]:  # 401/403 are expected without proper auth
                        print(f'✅ {name} server is reachable at {url}')
                    else:
                        print(f'⚠️  {name} server returned status {response.status}')
        except Exception as e:
            print(f'⚠️  {name} server not reachable at {url}: {e}')
            print(f'   This is normal if KM servers are not running yet')

asyncio.run(test_km_servers())
" 2>/dev/null || echo "⚠️  KM server connectivity test skipped"

# Create log directory
mkdir -p logs

# Set proper permissions
chmod 600 .env 2>/dev/null || true
chmod 755 logs 2>/dev/null || true

echo ""
echo "🎉 QuMail Secure Email Backend is ready to start!"
echo ""
echo "📋 Configuration Summary:"
echo "   • App Environment: $APP_ENV"
echo "   • Database: $(echo $DATABASE_URL | cut -d'@' -f2 | cut -d'/' -f1)"
echo "   • KM1 Server: $KM1_BASE_URL"
echo "   • KM2 Server: $KM2_BASE_URL"
echo "   • Google OAuth: $([ -n "$GOOGLE_CLIENT_ID" ] && [ "$GOOGLE_CLIENT_ID" != "your-google-oauth-client-id.apps.googleusercontent.com" ] && echo "Configured" || echo "Not configured")"
echo ""
echo "🚀 Starting server..."

# Start the FastAPI server
if [ "$APP_ENV" = "production" ]; then
    # Production mode with Gunicorn
    echo "🏭 Starting in production mode with Gunicorn..."
    exec gunicorn app.main:app \
        -w ${WORKERS:-4} \
        -k uvicorn.workers.UvicornWorker \
        --bind ${APP_HOST:-0.0.0.0}:${APP_PORT:-8000} \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --log-level ${LOG_LEVEL:-info} \
        --preload
else
    # Development mode with Uvicorn
    echo "🔧 Starting in development mode with Uvicorn..."
    exec uvicorn app.main:app \
        --host ${APP_HOST:-0.0.0.0} \
        --port ${APP_PORT:-8000} \
        --reload \
        --log-level ${LOG_LEVEL:-info} \
        --access-log
fi