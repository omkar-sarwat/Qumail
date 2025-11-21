#!/usr/bin/env python3
"""
QuMail Backend Validation Script

This script performs comprehensive testing of the QuMail secure email backend,
including KM server connectivity, encryption levels, database connectivity,
and OAuth configuration validation.
"""

import asyncio
import json
import os
import ssl
import sys
from pathlib import Path
from typing import Dict, List, Optional
import httpx
import asyncpg
import sqlite3
from cryptography.fernet import Fernet
from cryptography import x509
from cryptography.hazmat.primitives import serialization


class QuMailValidator:
    """Comprehensive validation for QuMail backend components."""
    
    def __init__(self, env_file: str = ".env"):
        """Initialize validator with environment configuration."""
        self.env_file = env_file
        self.config = {}
        self.results = {
            "environment": {"status": "pending", "details": []},
            "certificates": {"status": "pending", "details": []},
            "database": {"status": "pending", "details": []},
            "km_servers": {"status": "pending", "details": []},
            "google_oauth": {"status": "pending", "details": []},
            "encryption": {"status": "pending", "details": []},
            "dependencies": {"status": "pending", "details": []},
        }
    
    def load_environment(self) -> bool:
        """Load and validate environment configuration."""
        print("🔧 Loading environment configuration...")
        
        if not os.path.exists(self.env_file):
            self.results["environment"]["status"] = "failed"
            self.results["environment"]["details"].append(f"Environment file {self.env_file} not found")
            return False
        
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip().strip('"\'')
            
            # Validate required environment variables
            required_vars = [
                "SECRET_KEY", "ENCRYPTION_MASTER_KEY", "DATABASE_URL",
                "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI",
                "KM1_BASE_URL", "KM2_BASE_URL", "KM1_CLIENT_CERT_PFX", "KM2_CLIENT_CERT_PFX",
                "KM1_CA_CERT", "KM2_CA_CERT", "SENDER_SAE_ID", "RECEIVER_SAE_ID"
            ]
            
            missing_vars = [var for var in required_vars if var not in self.config]
            
            if missing_vars:
                self.results["environment"]["status"] = "failed"
                self.results["environment"]["details"].append(f"Missing required variables: {', '.join(missing_vars)}")
                return False
            
            # Validate SECRET_KEY length
            if len(self.config["SECRET_KEY"]) < 32:
                self.results["environment"]["status"] = "failed"
                self.results["environment"]["details"].append("SECRET_KEY must be at least 32 characters long")
                return False
            
            # Validate ENCRYPTION_MASTER_KEY (Fernet key)
            try:
                Fernet(self.config["ENCRYPTION_MASTER_KEY"].encode())
            except Exception as e:
                self.results["environment"]["status"] = "failed"
                self.results["environment"]["details"].append(f"Invalid ENCRYPTION_MASTER_KEY: {e}")
                return False
            
            self.results["environment"]["status"] = "passed"
            self.results["environment"]["details"].append("All required environment variables are present and valid")
            return True
            
        except Exception as e:
            self.results["environment"]["status"] = "failed"
            self.results["environment"]["details"].append(f"Error loading environment: {e}")
            return False
    
    def validate_certificates(self) -> bool:
        """Validate KM server certificates."""
        print("📜 Validating certificates...")
        
        cert_files = [
            ("KM1_CLIENT_CERT_PFX", self.config.get("KM1_CLIENT_CERT_PFX")),
            ("KM2_CLIENT_CERT_PFX", self.config.get("KM2_CLIENT_CERT_PFX")),
            ("KM1_CA_CERT", self.config.get("KM1_CA_CERT")),
            ("KM2_CA_CERT", self.config.get("KM2_CA_CERT"))
        ]
        
        all_valid = True
        
        for cert_name, cert_path in cert_files:
            if not cert_path:
                self.results["certificates"]["details"].append(f"{cert_name} not configured")
                all_valid = False
                continue
            
            cert_file = Path(cert_path)
            if not cert_file.exists():
                self.results["certificates"]["details"].append(f"{cert_name} file not found: {cert_path}")
                all_valid = False
                continue
            
            try:
                if cert_path.endswith('.pfx'):
                    # For PFX files, just check if they exist and are readable
                    with open(cert_path, 'rb') as f:
                        data = f.read()
                        if len(data) == 0:
                            self.results["certificates"]["details"].append(f"{cert_name} is empty")
                            all_valid = False
                        else:
                            self.results["certificates"]["details"].append(f"{cert_name} ✓")
                elif cert_path.endswith('.crt'):
                    # For certificate files, parse and validate
                    with open(cert_path, 'rb') as f:
                        cert_data = f.read()
                        cert = x509.load_pem_x509_certificate(cert_data)
                        self.results["certificates"]["details"].append(f"{cert_name} ✓ (expires: {cert.not_valid_after})")
                else:
                    self.results["certificates"]["details"].append(f"{cert_name} ✓")
                    
            except Exception as e:
                self.results["certificates"]["details"].append(f"{cert_name} validation failed: {e}")
                all_valid = False
        
        self.results["certificates"]["status"] = "passed" if all_valid else "failed"
        return all_valid
    
    async def validate_database(self) -> bool:
        """Validate database connectivity."""
        print("🗄️  Validating database connectivity...")
        
        database_url = self.config.get("DATABASE_URL", "")
        
        try:
            if database_url.startswith("postgresql"):
                # Test PostgreSQL connection
                conn = await asyncpg.connect(database_url.replace("postgresql+asyncpg://", "postgresql://"))
                result = await conn.fetchval("SELECT version()")
                await conn.close()
                self.results["database"]["details"].append(f"PostgreSQL connection successful: {result[:50]}...")
                
            elif database_url.startswith("sqlite"):
                # Test SQLite connection
                db_path = database_url.replace("sqlite+aiosqlite:///", "")
                if db_path.startswith("./"):
                    db_path = db_path[2:]
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                conn.close()
                self.results["database"]["details"].append(f"SQLite connection successful: version {version}")
            else:
                self.results["database"]["status"] = "failed"
                self.results["database"]["details"].append(f"Unsupported database URL: {database_url}")
                return False
            
            self.results["database"]["status"] = "passed"
            return True
            
        except Exception as e:
            self.results["database"]["status"] = "failed"
            self.results["database"]["details"].append(f"Database connection failed: {e}")
            return False
    
    async def validate_km_servers(self) -> bool:
        """Validate KM server connectivity."""
        print("🔐 Validating KM server connectivity...")
        
        km_servers = [
            ("KM1", self.config.get("KM1_BASE_URL")),
            ("KM2", self.config.get("KM2_BASE_URL"))
        ]
        
        all_valid = True
        
        for km_name, km_url in km_servers:
            if not km_url:
                self.results["km_servers"]["details"].append(f"{km_name} URL not configured")
                all_valid = False
                continue
            
            try:
                # Create SSL context that allows self-signed certificates
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    # Try to reach the server health endpoint
                    response = await client.get(f"{km_url}/health")
                    if response.status_code == 200:
                        self.results["km_servers"]["details"].append(f"{km_name} ✓ (status: {response.status_code})")
                    else:
                        # Try alternative endpoints
                        try:
                            response = await client.get(f"{km_url}/api/v1/keys/status")
                            self.results["km_servers"]["details"].append(f"{km_name} ✓ (API accessible)")
                        except:
                            response = await client.get(km_url)
                            self.results["km_servers"]["details"].append(f"{km_name} ~ (reachable but API unknown)")
                            
            except httpx.ConnectError:
                self.results["km_servers"]["details"].append(f"{km_name} ✗ (connection refused)")
                all_valid = False
            except Exception as e:
                self.results["km_servers"]["details"].append(f"{km_name} ✗ ({str(e)[:50]}...)")
                all_valid = False
        
        self.results["km_servers"]["status"] = "passed" if all_valid else "failed"
        return all_valid
    
    def validate_google_oauth(self) -> bool:
        """Validate Google OAuth configuration."""
        print("🔑 Validating Google OAuth configuration...")
        
        client_id = self.config.get("GOOGLE_CLIENT_ID", "")
        client_secret = self.config.get("GOOGLE_CLIENT_SECRET", "")
        redirect_uri = self.config.get("GOOGLE_REDIRECT_URI", "")
        
        all_valid = True
        
        # Validate client ID format
        if not client_id or not client_id.endswith(".apps.googleusercontent.com"):
            self.results["google_oauth"]["details"].append("GOOGLE_CLIENT_ID format appears invalid")
            all_valid = False
        else:
            self.results["google_oauth"]["details"].append("GOOGLE_CLIENT_ID format ✓")
        
        # Validate client secret
        if not client_secret or len(client_secret) < 20:
            self.results["google_oauth"]["details"].append("GOOGLE_CLIENT_SECRET appears invalid")
            all_valid = False
        else:
            self.results["google_oauth"]["details"].append("GOOGLE_CLIENT_SECRET ✓")
        
        # Validate redirect URI
        if not redirect_uri or not redirect_uri.startswith(("http://", "https://")):
            self.results["google_oauth"]["details"].append("GOOGLE_REDIRECT_URI format appears invalid")
            all_valid = False
        else:
            self.results["google_oauth"]["details"].append("GOOGLE_REDIRECT_URI format ✓")
        
        self.results["google_oauth"]["status"] = "passed" if all_valid else "failed"
        return all_valid
    
    def validate_encryption_setup(self) -> bool:
        """Validate encryption configuration."""
        print("🛡️  Validating encryption setup...")
        
        all_valid = True
        
        # Validate SAE IDs
        try:
            sender_sae_id = int(self.config.get("SENDER_SAE_ID", "0"))
            receiver_sae_id = int(self.config.get("RECEIVER_SAE_ID", "0"))
            
            if sender_sae_id <= 0 or receiver_sae_id <= 0:
                self.results["encryption"]["details"].append("SAE IDs must be positive integers")
                all_valid = False
            elif sender_sae_id == receiver_sae_id:
                self.results["encryption"]["details"].append("SENDER_SAE_ID and RECEIVER_SAE_ID must be different")
                all_valid = False
            else:
                self.results["encryption"]["details"].append(f"SAE IDs ✓ (sender: {sender_sae_id}, receiver: {receiver_sae_id})")
                
        except ValueError:
            self.results["encryption"]["details"].append("SAE IDs must be valid integers")
            all_valid = False
        
        # Test Fernet encryption
        try:
            fernet_key = self.config.get("ENCRYPTION_MASTER_KEY", "").encode()
            fernet = Fernet(fernet_key)
            test_data = b"test encryption"
            encrypted = fernet.encrypt(test_data)
            decrypted = fernet.decrypt(encrypted)
            
            if decrypted == test_data:
                self.results["encryption"]["details"].append("Fernet encryption test ✓")
            else:
                self.results["encryption"]["details"].append("Fernet encryption test failed")
                all_valid = False
                
        except Exception as e:
            self.results["encryption"]["details"].append(f"Fernet encryption test failed: {e}")
            all_valid = False
        
        self.results["encryption"]["status"] = "passed" if all_valid else "failed"
        return all_valid
    
    def validate_dependencies(self) -> bool:
        """Validate Python dependencies."""
        print("📦 Validating dependencies...")
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "alembic", "asyncpg",
            "httpx", "cryptography", "google-auth", "google-auth-oauthlib",
            "google-api-python-client", "pydantic", "python-jose", "passlib",
            "python-multipart", "aiofiles", "slowapi", "pycryptodome", "pqcrypto"
        ]
        
        all_valid = True
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.results["dependencies"]["details"].append(f"{package} ✓")
            except ImportError:
                self.results["dependencies"]["details"].append(f"{package} ✗ (not installed)")
                all_valid = False
        
        self.results["dependencies"]["status"] = "passed" if all_valid else "failed"
        return all_valid
    
    def print_results(self):
        """Print validation results."""
        print("\n" + "="*80)
        print("🔍 QUMAIL BACKEND VALIDATION RESULTS")
        print("="*80)
        
        overall_status = "PASSED"
        
        for category, result in self.results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏳"
            print(f"\n{status_icon} {category.upper().replace('_', ' ')}: {result['status'].upper()}")
            
            for detail in result["details"]:
                print(f"   • {detail}")
            
            if result["status"] == "failed":
                overall_status = "FAILED"
        
        print("\n" + "="*80)
        status_icon = "✅" if overall_status == "PASSED" else "❌"
        print(f"{status_icon} OVERALL STATUS: {overall_status}")
        print("="*80)
        
        if overall_status == "FAILED":
            print("\n🔧 RECOMMENDATIONS:")
            print("   • Fix all failed validations before starting the backend")
            print("   • Ensure qkd_kme_server-master is running on ports 13000 and 14000")
            print("   • Verify certificate paths and validity")
            print("   • Check database connectivity")
            print("   • Install missing Python dependencies")
            print("   • Validate Google OAuth configuration")
        else:
            print("\n🚀 Backend is ready to start!")
            print("   • Run: ./start.sh")
            print("   • Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    async def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 Starting QuMail Backend Validation")
        print("="*80)
        
        # Load environment first
        if not self.load_environment():
            self.print_results()
            return False
        
        # Run all validations
        validations = [
            self.validate_certificates(),
            await self.validate_database(),
            await self.validate_km_servers(),
            self.validate_google_oauth(),
            self.validate_encryption_setup(),
            self.validate_dependencies()
        ]
        
        self.print_results()
        return all(validations)


async def main():
    """Main validation function."""
    # Check if .env file exists
    env_file = ".env"
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        print("📋 Please copy .env.example to .env and configure it:")
        print("   cp .env.example .env")
        print("   # Edit .env with your actual configuration values")
        return False
    
    validator = QuMailValidator(env_file)
    success = await validator.run_all_validations()
    
    return success


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏸️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(1)