"""
QuMail Demo Data Setup Script
Creates realistic mock data in MongoDB for demonstration to judges.
Run this script to populate the database with sample encrypted emails,
quantum keys, and user data.
"""

import asyncio
import uuid
import base64
import hashlib
import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection - use environment variable or local fallback
MONGO_URL = os.getenv("DATABASE_URL", "mongodb://127.0.0.1:27017/qumail?directConnection=true")

# Try to use certifi for SSL certificates
try:
    import certifi
    CA_FILE = certifi.where()
except ImportError:
    CA_FILE = None

# Demo users
DEMO_USERS = [
    {
        "email": "alice.quantum@qumail.app",
        "display_name": "Alice Quantum",
        "role": "Quantum Security Researcher"
    },
    {
        "email": "bob.secure@qumail.app", 
        "display_name": "Bob Secure",
        "role": "Chief Security Officer"
    },
    {
        "email": "carol.crypto@qumail.app",
        "display_name": "Carol Crypto",
        "role": "Cryptography Engineer"
    },
    {
        "email": "david.defense@qumail.app",
        "display_name": "David Defense",
        "role": "Defense Systems Analyst"
    },
    {
        "email": "eve.enterprise@qumail.app",
        "display_name": "Eve Enterprise",
        "role": "Enterprise Security Manager"
    }
]

# Demo email subjects and bodies for different security levels
DEMO_EMAILS = [
    # Level 1 - OTP (Maximum Security)
    {
        "subject": "TOP SECRET: Quantum Key Distribution Protocol Update",
        "body": """Dear Team,

I'm pleased to announce that our Quantum Key Distribution (QKD) protocol has been successfully upgraded to support the ETSI GS QKD 014 standard.

Key highlights:
• Perfect forward secrecy using one-time pad encryption
• Quantum-resistant key exchange mechanism
• Real-time key synchronization between KME servers
• Entropy verification for all quantum keys

This communication is protected by Level 1 (OTP) encryption - the highest security level available, providing information-theoretic security.

Best regards,
Alice Quantum
Quantum Security Researcher""",
        "security_level": 1,
        "algorithm": "OTP-256"
    },
    {
        "subject": "CLASSIFIED: New Quantum-Safe Encryption Standards",
        "body": """Attention Security Council,

Following our review of post-quantum cryptographic standards, I recommend immediate implementation of the following protocols:

1. ML-KEM-1024 for key encapsulation
2. ML-DSA-87 for digital signatures
3. Hybrid encryption combining classical and quantum-resistant algorithms

The attached analysis shows vulnerability timelines for current RSA-2048 and ECC-256 systems against quantum computers.

This message is encrypted using OTP (One-Time Pad) - mathematically proven unbreakable encryption.

Regards,
Bob Secure
Chief Security Officer""",
        "security_level": 1,
        "algorithm": "OTP-256"
    },
    # Level 2 - AES with Quantum Keys
    {
        "subject": "Project Quantum Shield - Weekly Status Report",
        "body": """Hi Team,

Here's our weekly progress on Project Quantum Shield:

✅ Completed:
- KME server deployment on cloud infrastructure
- Cross-SAE key distribution testing
- Mobile app quantum encryption module

🔄 In Progress:
- Performance optimization for high-volume key generation
- Integration with enterprise email systems
- Security audit preparation

📅 Next Week:
- Final penetration testing
- Documentation review
- Demo preparation for stakeholders

This email uses AES-256-GCM encryption with quantum-derived keys for enhanced security.

Carol Crypto
Cryptography Engineer""",
        "security_level": 2,
        "algorithm": "AES-256-GCM"
    },
    {
        "subject": "Quantum Key Pool Status Alert",
        "body": """System Notification,

The quantum key pool has been replenished with fresh keys from the KME servers.

Current Status:
• Total Keys Available: 10,000
• Keys Used Today: 2,847
• Entropy Score: 0.9987 (Excellent)
• Key Refresh Rate: 500 keys/minute

All keys have been verified against NIST SP 800-90B entropy requirements.

This automated message is secured with AES-256-GCM using quantum-enhanced key material.

QuMail Security System""",
        "security_level": 2,
        "algorithm": "AES-256-GCM"
    },
    # Level 3 - Post-Quantum Cryptography
    {
        "subject": "Post-Quantum Migration Roadmap",
        "body": """Dear Leadership Team,

As quantum computing advances, I've prepared our migration strategy to post-quantum cryptographic standards:

Phase 1 (Current): Hybrid Implementation
- Combine classical RSA/ECC with ML-KEM
- Dual signatures using ECDSA + ML-DSA

Phase 2 (Q2 2025): Full PQC Deployment
- Complete migration to NIST-approved algorithms
- Retire vulnerable classical cryptography

Phase 3 (Q4 2025): Quantum Key Distribution
- Deploy dedicated QKD links for critical infrastructure
- Implement quantum random number generators

This message uses ML-KEM-1024 (Kyber) for key encapsulation and ML-DSA-87 (Dilithium) for signatures.

David Defense
Defense Systems Analyst""",
        "security_level": 3,
        "algorithm": "ML-KEM-1024 + ML-DSA-87"
    },
    # Level 4 - Standard RSA
    {
        "subject": "Enterprise Security Newsletter - December 2024",
        "body": """QuMail Enterprise Security Update

Welcome to our monthly security newsletter!

🔐 New Features:
- Multi-factor authentication with hardware tokens
- Enhanced audit logging
- Real-time threat detection

📊 Security Metrics This Month:
- 0 security incidents
- 100% uptime
- 50,000+ encrypted messages processed

🏆 Recognition:
QuMail has been certified compliant with:
- ISO 27001
- SOC 2 Type II
- GDPR

Stay secure!
Eve Enterprise
Enterprise Security Manager""",
        "security_level": 4,
        "algorithm": "RSA-4096 + AES-256"
    }
]

# QKD Key data for demo
def generate_mock_key_material() -> str:
    """Generate mock quantum key material (base64 encoded)"""
    key_bytes = os.urandom(32)  # 256 bits
    return base64.b64encode(key_bytes).decode('utf-8')

def generate_mock_ciphertext(plaintext: str, security_level: int) -> str:
    """Generate mock encrypted content (for demo purposes)"""
    # Create a realistic-looking ciphertext
    message_bytes = plaintext.encode('utf-8')
    # XOR with random bytes to create "encrypted" looking data
    random_key = os.urandom(len(message_bytes))
    encrypted = bytes(a ^ b for a, b in zip(message_bytes, random_key * (len(message_bytes) // len(random_key) + 1)))
    return base64.b64encode(encrypted).decode('utf-8')

async def setup_demo_database():
    """Main function to set up demo data"""
    print("🚀 QuMail Demo Data Setup")
    print("=" * 50)
    
    # Connect to MongoDB Atlas
    print("\n📡 Connecting to MongoDB Atlas...")
    
    # Build connection options for Atlas
    connection_options = {
        "serverSelectionTimeoutMS": 60000,
        "connectTimeoutMS": 60000,
        "socketTimeoutMS": 60000,
        "tlsAllowInvalidCertificates": True,
    }
    
    if CA_FILE:
        connection_options["tlsCAFile"] = CA_FILE
        print(f"  Using CA file: {CA_FILE}")
    
    client = AsyncIOMotorClient(MONGO_URL, **connection_options)
    db = client["qumail"]
    
    # Test connection
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        print("\n⚠️ Make sure your IP is whitelisted in MongoDB Atlas!")
        print("Go to: MongoDB Atlas → Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)")
        return
    
    # Collections
    users_col = db["users"]
    emails_col = db["emails"]
    qkd_keys_col = db["qkd_keys"]
    qkd_sessions_col = db["qkd_sessions"]
    qkd_audit_col = db["qkd_audit_logs"]
    encryption_metadata_col = db["encryption_metadata"]
    
    # Clear existing demo data (optional)
    print("\n🧹 Clearing existing demo data...")
    await users_col.delete_many({"email": {"$regex": "@qumail.app$"}})
    await emails_col.delete_many({"sender_email": {"$regex": "@qumail.app$"}})
    await qkd_keys_col.delete_many({"sender_email": {"$regex": "@qumail.app$"}})
    await qkd_sessions_col.delete_many({"sender_email": {"$regex": "@qumail.app$"}})
    
    # Create demo users
    print("\n👥 Creating demo users...")
    user_ids = {}
    for user_data in DEMO_USERS:
        user_id = str(uuid.uuid4())
        user_doc = {
            "_id": user_id,
            "email": user_data["email"],
            "display_name": user_data["display_name"],
            "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
            "last_login": datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            "totp_enabled": random.choice([True, False]),
            "totp_verified": True,
        }
        await users_col.insert_one(user_doc)
        user_ids[user_data["email"]] = user_id
        print(f"  ✅ Created user: {user_data['display_name']} ({user_data['email']})")
    
    # Create demo emails
    print("\n📧 Creating demo encrypted emails...")
    email_count = 0
    
    for i, email_data in enumerate(DEMO_EMAILS):
        # Select random sender and receiver
        sender = random.choice(DEMO_USERS)
        receiver = random.choice([u for u in DEMO_USERS if u["email"] != sender["email"]])
        
        flow_id = str(uuid.uuid4())
        email_id = str(uuid.uuid4())
        key_id = str(uuid.uuid4())
        
        # Create encrypted body (mock)
        message_json = json.dumps({
            "subject": email_data["subject"],
            "body": email_data["body"],
            "from": sender["email"],
            "to": receiver["email"],
            "timestamp": datetime.utcnow().isoformat()
        })
        encrypted_body = generate_mock_ciphertext(message_json, email_data["security_level"])
        
        # Create email document
        email_doc = {
            "_id": email_id,
            "flow_id": flow_id,
            "user_id": user_ids[sender["email"]],
            "sender_email": sender["email"],
            "receiver_email": receiver["email"],
            "allowed_emails": [sender["email"], receiver["email"]],
            "subject": f"[ENCRYPTED-L{email_data['security_level']}] {email_data['subject'][:50]}...",
            "body_encrypted": encrypted_body,
            "decrypted_body": message_json,  # Store decrypted for demo
            "encryption_key_id": key_id,
            "encryption_algorithm": email_data["algorithm"],
            "encryption_iv": base64.b64encode(os.urandom(12)).decode('utf-8'),
            "encryption_auth_tag": base64.b64encode(os.urandom(16)).decode('utf-8'),
            "encryption_metadata": {
                "flow_id": flow_id,
                "key_id": key_id,
                "algorithm": email_data["algorithm"],
                "security_level": email_data["security_level"],
                "quantum_enhanced": True,
                "entropy": round(random.uniform(0.98, 1.0), 4),
                "key_size": 256,
                "encrypted_size": len(encrypted_body)
            },
            "security_level": email_data["security_level"],
            "direction": "SENT",
            "timestamp": datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            "is_read": random.choice([True, False]),
            "is_starred": random.choice([True, False]),
            "is_suspicious": False,
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 168))
        }
        await emails_col.insert_one(email_doc)
        email_count += 1
        
        # Create corresponding QKD key
        qkd_key_doc = {
            "_id": str(uuid.uuid4()),
            "key_id": key_id,
            "kme1_key_id": str(uuid.uuid4()),
            "kme2_key_id": str(uuid.uuid4()),
            "key_material_encrypted": generate_mock_key_material(),
            "key_hash": hashlib.sha256(os.urandom(32)).hexdigest(),
            "key_size_bits": 256,
            "source_kme": "KME1",
            "sae1_id": "25840139-0dd4-49ae-ba1e-b86731601803",
            "sae2_id": "c565d5aa-8670-4446-8471-b0e53e315d2a",
            "sender_email": sender["email"],
            "receiver_email": receiver["email"],
            "flow_id": flow_id,
            "email_id": email_id,
            "security_level": email_data["security_level"],
            "algorithm": email_data["algorithm"],
            "state": "consumed",
            "is_consumed": True,
            "consumed_by": user_ids[sender["email"]],
            "consumed_at": datetime.utcnow(),
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "entropy_score": round(random.uniform(0.98, 1.0), 4),
            "quality_score": round(random.uniform(0.95, 1.0), 4),
            "quantum_grade": True,
            "operation_history": [
                {
                    "operation": "GENERATED",
                    "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(2, 170))).isoformat(),
                    "source": "KME1"
                },
                {
                    "operation": "USED_FOR_EMAIL_ENCRYPTION",
                    "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(1, 168))).isoformat(),
                    "flow_id": flow_id,
                    "security_level": email_data["security_level"]
                }
            ]
        }
        await qkd_keys_col.insert_one(qkd_key_doc)
        
        # Create QKD session
        session_doc = {
            "_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "flow_id": flow_id,
            "sender_email": sender["email"],
            "sender_sae_id": "25840139-0dd4-49ae-ba1e-b86731601803",
            "receiver_email": receiver["email"],
            "receiver_sae_id": "c565d5aa-8670-4446-8471-b0e53e315d2a",
            "kme1_endpoint": "https://qumail-kme1-pmsy.onrender.com",
            "kme2_endpoint": "https://qumail-kme2-pmsy.onrender.com",
            "key_ids": [key_id],
            "total_keys_used": 1,
            "total_bits_exchanged": 256,
            "is_active": False,
            "is_successful": True,
            "security_level": email_data["security_level"],
            "encryption_algorithm": email_data["algorithm"],
            "started_at": datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            "completed_at": datetime.utcnow() - timedelta(hours=random.randint(1, 167)),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        await qkd_sessions_col.insert_one(session_doc)
        
        # Create audit log entry
        audit_doc = {
            "_id": str(uuid.uuid4()),
            "operation": "EMAIL_ENCRYPTED",
            "key_id": key_id,
            "session_id": session_doc["session_id"],
            "flow_id": flow_id,
            "user_email": sender["email"],
            "user_id": user_ids[sender["email"]],
            "success": True,
            "details": {
                "security_level": email_data["security_level"],
                "algorithm": email_data["algorithm"],
                "receiver_email": receiver["email"],
                "encrypted_size": len(encrypted_body)
            },
            "timestamp": datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "user_agent": "QuMail Desktop v1.0"
        }
        await qkd_audit_col.insert_one(audit_doc)
        
        print(f"  ✅ Email {i+1}: {email_data['subject'][:40]}... (Level {email_data['security_level']})")
    
    # Create additional available quantum keys in the pool
    print("\n🔑 Creating quantum key pool...")
    available_keys = []
    for i in range(50):
        key_doc = {
            "_id": str(uuid.uuid4()),
            "key_id": str(uuid.uuid4()),
            "kme1_key_id": str(uuid.uuid4()),
            "key_material_encrypted": generate_mock_key_material(),
            "key_hash": hashlib.sha256(os.urandom(32)).hexdigest(),
            "key_size_bits": 256,
            "source_kme": random.choice(["KME1", "KME2"]),
            "sae1_id": "25840139-0dd4-49ae-ba1e-b86731601803",
            "sae2_id": "c565d5aa-8670-4446-8471-b0e53e315d2a",
            "security_level": 1,
            "state": "ready",
            "is_consumed": False,
            "created_at": datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "entropy_score": round(random.uniform(0.98, 1.0), 4),
            "quality_score": round(random.uniform(0.95, 1.0), 4),
            "quantum_grade": True
        }
        available_keys.append(key_doc)
    
    if available_keys:
        await qkd_keys_col.insert_many(available_keys)
    print(f"  ✅ Created {len(available_keys)} available quantum keys in pool")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 DEMO DATA SUMMARY")
    print("=" * 50)
    print(f"  👥 Users created: {len(DEMO_USERS)}")
    print(f"  📧 Encrypted emails: {email_count}")
    print(f"  🔑 Quantum keys (used): {email_count}")
    print(f"  🔑 Quantum keys (available): {len(available_keys)}")
    print(f"  📋 QKD sessions: {email_count}")
    print(f"  📝 Audit logs: {email_count}")
    
    print("\n✨ Demo data setup complete!")
    print("\n📌 Demo User Accounts:")
    for user in DEMO_USERS:
        print(f"   • {user['display_name']} - {user['email']}")
    
    print("\n🔒 Security Levels Demonstrated:")
    print("   • Level 1: OTP (One-Time Pad) - Information-theoretic security")
    print("   • Level 2: AES-256-GCM with quantum keys")
    print("   • Level 3: Post-Quantum Cryptography (ML-KEM + ML-DSA)")
    print("   • Level 4: RSA-4096 + AES-256")
    
    # Close connection
    client.close()
    print("\n✅ Database connection closed.")

if __name__ == "__main__":
    asyncio.run(setup_demo_database())
