"""
QuMail SQLite Database Viewer
=============================
This script displays all SQLite databases used by QuMail for judges/reviewers.

Run: python show_sqlite_databases.py
"""
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title: str):
    print("\n" + "-" * 60)
    print(f"  {title}")
    print("-" * 60)

def show_backend_private_keys():
    """Show the backend SQLite database storing private keys for Level 3/4"""
    db_path = Path(__file__).parent / "app" / "data" / "private_keys.db"
    
    print_header("BACKEND: Private Keys Database")
    print(f"\n📁 Location: {db_path}")
    
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    print(f"📊 File Size: {db_path.stat().st_size:,} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Show table schema
        print_section("Table Schema")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='private_keys'")
        schema = cursor.fetchone()
        if schema:
            print(schema[0])
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM private_keys")
        total = cursor.fetchone()[0]
        print(f"\n📈 Total Records: {total}")
        
        # Count by level
        cursor.execute("SELECT level, COUNT(*) FROM private_keys GROUP BY level")
        counts = cursor.fetchall()
        print("\n📊 Records by Security Level:")
        for level, count in counts:
            level_name = "PQC (ML-KEM + ML-DSA)" if level == 3 else "RSA-4096"
            print(f"   Level {level} ({level_name}): {count} private keys")
        
        # Show sample records (with truncated keys for security)
        print_section("Sample Records (keys truncated for display)")
        cursor.execute("SELECT flow_id, level, private_key_json, created_at FROM private_keys ORDER BY created_at DESC LIMIT 5")
        rows = cursor.fetchall()
        
        for i, (flow_id, level, key_json, created_at) in enumerate(rows, 1):
            print(f"\n[{i}] Flow ID: {flow_id}")
            print(f"    Security Level: {level}")
            print(f"    Created: {created_at}")
            
            try:
                keys = json.loads(key_json)
                print(f"    Keys stored:")
                for key_name, key_value in keys.items():
                    # Show first 50 chars of each key
                    truncated = key_value[:50] + "..." if len(key_value) > 50 else key_value
                    print(f"      - {key_name}: {truncated} ({len(key_value)} chars)")
            except:
                print(f"    Keys: [unable to parse]")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

def show_frontend_electron_db():
    """Show the Electron frontend SQLite database for decrypted email cache"""
    # Standard Electron userData paths
    app_data = os.environ.get('APPDATA', '')
    possible_paths = [
        Path(app_data) / "Electron" / "qumail.db",
        Path(app_data) / "qumail-electron" / "qumail.db",
        Path(app_data) / "QuMail" / "qumail.db",
    ]
    
    print_header("FRONTEND: Electron Decrypted Email Cache")
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print(f"\n📁 Expected Location: {possible_paths[0]}")
        print("❌ Database not found (Electron app may not have been run yet)")
        return
    
    print(f"\n📁 Location: {db_path}")
    print(f"📊 File Size: {db_path.stat().st_size:,} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📋 Tables: {[t[0] for t in tables]}")
        
        for table_name, in tables:
            print_section(f"Table: {table_name}")
            
            # Show schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            schema = cursor.fetchone()
            if schema:
                print(schema[0])
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nRecords: {count}")
            
            # Show sample data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"Sample data (first 3 rows):")
                for row in rows:
                    print(f"\n  Record:")
                    for col, val in zip(columns, row):
                        if isinstance(val, str) and len(val) > 100:
                            val = val[:100] + "..."
                        print(f"    {col}: {val}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

def show_summary():
    """Show summary of all databases"""
    print_header("QuMail SQLite DATABASE SUMMARY")
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        QuMail Key Storage Architecture                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                         MONGODB ATLAS (Cloud)                           │ ║
║  │  Database: qumail | Collection: emails                                  │ ║
║  │                                                                         │ ║
║  │  Stores:                                                                │ ║
║  │  • Encrypted email content (body_encrypted)                             │ ║
║  │  • PUBLIC keys only (rsa_public_key, kem_public_key, dsa_public_key)    │ ║
║  │  • Encryption metadata (algorithm, nonce, auth_tag, etc.)               │ ║
║  │  • Email metadata (sender, receiver, subject, timestamp)                │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                    │                                         ║
║                                    │ Public keys sent to cloud               ║
║                                    │ Private keys NEVER leave local          ║
║                                    ▼                                         ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                    BACKEND SQLite (Local Server)                        │ ║
║  │  File: qumail-backend/app/data/private_keys.db                          │ ║
║  │                                                                         │ ║
║  │  Stores PRIVATE keys for Level 3 & 4:                                   │ ║
║  │  • Level 3: kem_secret_key (ML-KEM-1024), dsa_secret_key (ML-DSA-87)    │ ║
║  │  • Level 4: rsa_private_key (RSA-4096)                                  │ ║
║  │  • flow_id links to MongoDB email record                                │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                   FRONTEND SQLite (Electron App)                        │ ║
║  │  File: %AppData%/Electron/qumail.db                                     │ ║
║  │                                                                         │ ║
║  │  Stores:                                                                │ ║
║  │  • Cached decrypted email content (for offline viewing)                 │ ║
║  │  • Session data                                                         │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SECURITY: Private keys are stored locally and NEVER transmitted to cloud   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def main():
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "       QuMail SQLite Database Viewer - For Judges/Reviewers".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    show_summary()
    show_backend_private_keys()
    show_frontend_electron_db()
    
    print("\n" + "=" * 80)
    print("  END OF DATABASE REPORT")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
