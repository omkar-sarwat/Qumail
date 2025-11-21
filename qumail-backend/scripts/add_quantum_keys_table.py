"""
Add quantum_keys table for proper key lifecycle management
Run this script to update your database schema
"""
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def add_quantum_keys_table():
    """Add quantum_keys table to store quantum key material"""
    
    db_path = project_root / "qumail.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='quantum_keys'
        """)
        
        if cursor.fetchone():
            print("✓ quantum_keys table already exists")
            return True
        
        print("Creating quantum_keys table...")
        
        cursor.execute("""
            CREATE TABLE quantum_keys (
                id VARCHAR(36) PRIMARY KEY,
                kme1_key_id VARCHAR(255) NOT NULL,
                kme2_key_id VARCHAR(255) NOT NULL,
                kme1_key_material BLOB NOT NULL,
                kme2_key_material BLOB NOT NULL,
                key_size_bits INTEGER NOT NULL,
                algorithm VARCHAR(50) DEFAULT 'OTP-QKD',
                state VARCHAR(20) DEFAULT 'GENERATED',
                generated_at DATETIME NOT NULL,
                reserved_at DATETIME,
                consumed_at DATETIME,
                used_by_email VARCHAR(255),
                used_for_flow_id VARCHAR(255),
                source_kme1_sae VARCHAR(100),
                source_kme2_sae VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_quantum_keys_kme1_key_id ON quantum_keys(kme1_key_id)")
        cursor.execute("CREATE INDEX idx_quantum_keys_kme2_key_id ON quantum_keys(kme2_key_id)")
        cursor.execute("CREATE INDEX idx_quantum_keys_state ON quantum_keys(state)")
        cursor.execute("CREATE INDEX idx_quantum_keys_flow_id ON quantum_keys(used_for_flow_id)")
        
        conn.commit()
        print("✓ quantum_keys table created successfully")
        print("✓ Indexes created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating quantum_keys table: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("QuMail Database Migration: Add Quantum Keys Table")
    print("="*60)
    print()
    
    success = add_quantum_keys_table()
    
    print()
    if success:
        print("="*60)
        print("Migration completed successfully!")
        print("="*60)
    else:
        print("="*60)
        print("Migration failed!")
        print("="*60)
        sys.exit(1)
