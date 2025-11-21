"""Add the `encryption_metadata` column to the emails table if it is missing.

Run with: `python scripts/add_encryption_metadata_column.py`
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def main() -> int:
    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        print("This utility only supports SQLite databases.")
        return 1

    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    db_path = db_path.lstrip("/") if db_path.startswith("/") else db_path
    resolved = Path(db_path).resolve()

    if not resolved.exists():
        print(f"Database file not found at {resolved}")
        return 1

    conn = sqlite3.connect(str(resolved))
    cursor = conn.cursor()

    try:
        if not column_exists(cursor, "emails", "encryption_metadata"):
            print("Adding encryption_metadata column to emails table...")
            cursor.execute("ALTER TABLE emails ADD COLUMN encryption_metadata TEXT")
        else:
            print("encryption_metadata column already present – skipping ALTER TABLE")

        print("Backfilling encryption_metadata for existing emails...")
        cursor.execute(
            """
            UPDATE emails
               SET encryption_metadata = '{}'
             WHERE encryption_metadata IS NULL
            """
        )

        conn.commit()
        print("Database update complete.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
