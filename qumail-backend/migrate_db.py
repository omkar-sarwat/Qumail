"""
Database migration script to add encryption_key_id column
"""
import asyncio
import sqlite3
import os

async def migrate():
    db_path = "qumail.db"
    
    if not os.path.exists(db_path):
        print(f"✗ Database not found at {db_path}")
        return
    
    print(f"📊 Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(emails)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add all missing encryption columns
    encryption_columns = {
        'encryption_key_id': 'VARCHAR(255)',
        'encryption_algorithm': 'VARCHAR(100)',
        'encryption_iv': 'TEXT',
        'encryption_auth_tag': 'TEXT',
        'encryption_metadata': 'TEXT'  # JSON stored as TEXT
    }
    
    for col_name, col_type in encryption_columns.items():
        if col_name in columns:
            print(f"✓ {col_name} column already exists")
        else:
            print(f"Adding {col_name} column...")
            try:
                cursor.execute(f"""
                    ALTER TABLE emails 
                    ADD COLUMN {col_name} {col_type}
                """)
                if col_name == 'encryption_key_id':
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS ix_emails_encryption_key_id 
                        ON emails(encryption_key_id)
                    """)
                conn.commit()
                print(f"✓ {col_name} column added successfully")
            except Exception as e:
                print(f"✗ Failed to add {col_name}: {e}")
    
    # Verify all encryption columns exist
    required_columns = [
        'encryption_key_id',
        'encryption_algorithm', 
        'encryption_iv',
        'encryption_auth_tag',
        'encryption_metadata'
    ]
    
    cursor.execute("PRAGMA table_info(emails)")
    columns = [col[1] for col in cursor.fetchall()]
    
    missing = [col for col in required_columns if col not in columns]
    if missing:
        print(f"⚠️  Missing columns: {missing}")
    else:
        print("✓ All encryption columns present")
    
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
