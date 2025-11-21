# QuMail Backend Development Guide

This guide provides comprehensive instructions for setting up, developing, and testing the QuMail secure email backend.

## 🚀 Quick Start Guide

### 1. Prerequisites Setup

Ensure you have the following installed:
- **Python 3.11+** - Required for modern async features
- **Docker & Docker Compose** - For database and development environment
- **Git** - For version control
- **OpenSSL** - For certificate operations

### 2. Clone and Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd qumail-secure-email/qumail-backend

# Make scripts executable (Linux/macOS)
chmod +x start.sh validate_backend.py

# Copy environment template
cp .env.example .env
```

### 3. Environment Configuration

Edit `.env` file with your specific configuration:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Configure Google OAuth (required for Gmail integration)
# 1. Go to https://console.cloud.google.com/
# 2. Create a new project or select existing
# 3. Enable Gmail API
# 4. Create OAuth 2.0 credentials
# 5. Add redirect URI: http://localhost:3000/auth/callback
```

### 4. Start Development Environment

#### Option A: Docker Compose (Recommended)
```bash
# Start all services (PostgreSQL, Redis, Backend)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f qumail-backend
```

#### Option B: Local Development
```bash
# Validate configuration first
python validate_backend.py

# Start with the startup script
./start.sh

# Or manually
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

```bash
# Check API documentation
open http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health

# Validate backend configuration
python validate_backend.py
```

## 🏗️ Development Workflow

### Project Structure

```
qumail-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup and connection
│   ├── api/                 # API route definitions
│   │   ├── encryption_routes.py
│   │   └── gmail_routes.py
│   ├── core/                # Core security services
│   │   ├── km_client.py     # KM server client
│   │   ├── security_auditor.py
│   │   └── encryption/      # Four encryption levels
│   ├── middleware/          # Custom middleware
│   │   └── error_handling.py
│   ├── models/              # Database and Pydantic models
│   │   ├── database.py
│   │   ├── requests.py
│   │   └── responses.py
│   └── services/            # Business logic services
│       ├── gmail_oauth.py
│       └── gmail_client.py
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── docker/                  # Docker configuration
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── docker-compose.yml      # Development environment
├── start.sh                # Startup script
├── validate_backend.py     # Configuration validator
└── README.md               # This file
```

### Adding New Features

#### 1. Create a New API Endpoint

```python
# app/api/new_feature_routes.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.security_auditor import SecurityAuditor

router = APIRouter(prefix="/api/v1/feature", tags=["feature"])

@router.post("/action")
async def perform_action(
    request: ActionRequest,
    auditor: SecurityAuditor = Depends(SecurityAuditor)
):
    """Perform a new action with security auditing."""
    try:
        # Log security event
        await auditor.log_event(
            event_type="feature_action",
            user_id=request.user_id,
            details={"action": "perform_action"}
        )
        
        # Your business logic here
        result = await some_business_logic(request)
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        await auditor.log_security_incident(
            incident_type="feature_error",
            severity="medium",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Action failed")
```

#### 2. Register the Router

```python
# app/main.py
from app.api.new_feature_routes import router as feature_router

app.include_router(feature_router)
```

#### 3. Add Request/Response Models

```python
# app/models/requests.py
from pydantic import BaseModel, Field

class ActionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    action_data: dict = Field(..., description="Action parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user@example.com",
                "action_data": {"param1": "value1"}
            }
        }
```

### Database Migrations

#### Creating a New Migration

```bash
# Generate migration for model changes
alembic revision --autogenerate -m "Add new feature table"

# Review the generated migration file in alembic/versions/
# Edit if necessary, then apply
alembic upgrade head
```

#### Migration Best Practices

1. **Always review auto-generated migrations**
2. **Test migrations on development data**
3. **Include rollback strategies**
4. **Document schema changes**

### Testing

#### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-httpx pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_encryption.py

# Run specific test
pytest tests/test_encryption.py::test_level1_encryption -v
```

#### Writing Tests

```python
# tests/test_new_feature.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_new_feature_endpoint():
    """Test new feature endpoint."""
    response = client.post("/api/v1/feature/action", json={
        "user_id": "test@example.com",
        "action_data": {"test": "data"}
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## 🔧 Configuration Management

### Environment Variables

The application uses environment variables for configuration. Key categories:

#### Application Settings
- `APP_NAME` - Application name
- `APP_VERSION` - Version identifier
- `APP_ENV` - Environment (development/production)
- `DEBUG` - Debug mode flag
- `LOG_LEVEL` - Logging level

#### Security Configuration
- `SECRET_KEY` - JWT signing key (minimum 32 characters)
- `ENCRYPTION_MASTER_KEY` - Fernet encryption key
- `SESSION_TIMEOUT` - Session timeout in minutes

#### Database Settings
- `DATABASE_URL` - Database connection string
- `DB_POOL_SIZE` - Connection pool size
- `DB_MAX_OVERFLOW` - Maximum pool overflow

#### External Services
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GOOGLE_REDIRECT_URI` - OAuth redirect URI

#### KM Server Configuration
- `KM1_BASE_URL` - First KM server URL
- `KM2_BASE_URL` - Second KM server URL
- `KM1_CLIENT_CERT_PFX` - Client certificate for KM1
- `KM2_CLIENT_CERT_PFX` - Client certificate for KM2
- `KM1_CA_CERT` - CA certificate for KM1
- `KM2_CA_CERT` - CA certificate for KM2
- `SENDER_SAE_ID` - Sender SAE identifier
- `RECEIVER_SAE_ID` - Receiver SAE identifier

### Configuration Validation

Use the validation script to check configuration:

```bash
python validate_backend.py
```

This will check:
- ✅ Environment variables presence and format
- ✅ Certificate file existence and validity
- ✅ Database connectivity
- ✅ KM server reachability
- ✅ Google OAuth configuration
- ✅ Encryption setup
- ✅ Python dependencies

## 🔐 Security Development Guidelines

### 1. Authentication and Authorization

```python
# Always use proper authentication decorators
from app.core.auth import require_authentication

@router.post("/secure-endpoint")
async def secure_endpoint(
    request: Request,
    current_user: User = Depends(require_authentication)
):
    # Your secure logic here
    pass
```

### 2. Input Validation

```python
# Use Pydantic models for input validation
from pydantic import BaseModel, Field, validator

class SecureRequest(BaseModel):
    data: str = Field(..., min_length=1, max_length=1000)
    
    @validator('data')
    def validate_data(cls, v):
        # Custom validation logic
        if not v.strip():
            raise ValueError('Data cannot be empty')
        return v
```

### 3. Error Handling

```python
# Use security-aware error handling
from app.middleware.error_handling import SecurityAwareException

try:
    # Risky operation
    result = await risky_operation()
except Exception as e:
    # Log security incident
    await auditor.log_security_incident(
        incident_type="operation_failure",
        severity="medium",
        details={"operation": "risky_operation", "error": str(e)}
    )
    raise SecurityAwareException("Operation failed", status_code=500)
```

### 4. Logging and Auditing

```python
# Always log security-relevant events
await auditor.log_event(
    event_type="data_access",
    user_id=user.id,
    details={
        "resource": "sensitive_data",
        "action": "read",
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

## 🔍 Debugging and Troubleshooting

### Common Issues and Solutions

#### 1. KM Server Connection Issues

**Problem**: `KM server not reachable`

**Solutions**:
```bash
# Check if KM servers are running
curl -k https://localhost:13000/health
curl -k https://localhost:14000/health

# Verify certificate paths
ls -la ../qkd_kme_server-master/certs/kme-1-local-zone/
ls -la ../qkd_kme_server-master/certs/kme-2-local-zone/

# Check configuration
grep KM .env
```

#### 2. Database Connection Issues

**Problem**: `Database connection failed`

**Solutions**:
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection manually
psql postgresql://qumail_user:secure_password@localhost:5432/qumail

# Check database logs
docker-compose logs postgres
```

#### 3. OAuth Configuration Issues

**Problem**: `invalid_client` error

**Solutions**:
1. Verify Google Cloud Console configuration
2. Check client ID format (must end with `.apps.googleusercontent.com`)
3. Ensure redirect URI matches exactly
4. Verify Gmail API is enabled

#### 4. Certificate Issues

**Problem**: `certificate verify failed`

**Solutions**:
```bash
# Check certificate validity
openssl x509 -in ../qkd_kme_server-master/certs/kme-1-local-zone/ca.crt -text -noout

# Verify PFX files
openssl pkcs12 -info -in ../qkd_kme_server-master/certs/kme-1-local-zone/client_1.pfx -noout
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Restart the application
./start.sh
```

### Logging

View application logs:

```bash
# Docker environment
docker-compose logs -f qumail-backend

# Local development
tail -f qumail-backend.log

# Specific log levels
grep ERROR qumail-backend.log
grep WARNING qumail-backend.log
```

## 📊 Performance Optimization

### Database Optimization

1. **Use Connection Pooling**
```python
# In database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)
```

2. **Optimize Queries**
```python
# Use select specific columns
result = await session.execute(
    select(User.id, User.email).where(User.active == True)
)

# Use eager loading for relationships
result = await session.execute(
    select(User).options(selectinload(User.sessions))
)
```

### Caching

```python
# Use Redis for caching
from app.core.cache import cache_manager

@cache_manager.cached(ttl=300)  # 5 minutes
async def expensive_operation(param: str):
    # Expensive computation
    return result
```

### Async Best Practices

```python
# Use async/await properly
async def process_multiple_items(items: List[str]):
    # Process items concurrently
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

## 🚀 Deployment Guide

### Development Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Verify deployment
curl http://localhost:8000/health
```

### Production Deployment

1. **Update Environment Configuration**
```bash
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/qumail
```

2. **Use Production Database**
```bash
# PostgreSQL with proper backup and monitoring
# Configure connection pooling
# Set up read replicas if needed
```

3. **SSL/TLS Configuration**
```bash
# Use proper SSL certificates
# Configure HTTPS endpoints
# Set up certificate auto-renewal
```

4. **Monitoring and Logging**
```bash
# Set up log aggregation
# Configure health check monitoring
# Set up alerting for critical events
```

### Production Checklist

- [ ] Change all default passwords and keys
- [ ] Use production database (PostgreSQL)
- [ ] Enable HTTPS with valid certificates
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and alerting
- [ ] Configure log rotation
- [ ] Implement backup strategy
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable security headers

## 📚 Additional Resources

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [ETSI GS QKD-014 Standard](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_QKD014v010101p.pdf)
- [Google Gmail API](https://developers.google.com/gmail/api)

### Development Tools
- **Database Admin**: http://localhost:5050 (PgAdmin)
- **Redis Admin**: http://localhost:8081 (Redis Commander)
- **API Testing**: Use Postman or HTTPie

### Support and Contribution

1. **Issues**: Report bugs and feature requests via GitHub issues
2. **Contributing**: Follow the contribution guidelines
3. **Code Review**: All changes require peer review
4. **Testing**: Maintain test coverage above 80%

---

**Happy Coding! 🚀**

Remember to always prioritize security, follow best practices, and test thoroughly before deploying to production.