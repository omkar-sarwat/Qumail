"""Utility script to backfill the `user_id` column on the emails table.

Run with: `python scripts/add_user_id_column.py`
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` imports succeed when running directly.
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
        if not column_exists(cursor, "emails", "user_id"):
            print("Adding user_id column to emails table...")
            cursor.execute("ALTER TABLE emails ADD COLUMN user_id INTEGER")
        else:
            print("user_id column already present – skipping ALTER TABLE")

        # Populate user_id for existing rows where possible
        print("Backfilling user_id values using sender_email matches...")
        cursor.execute(
            """
            UPDATE emails
               SET user_id = (
                   SELECT id FROM users WHERE users.email = emails.sender_email
               )
             WHERE user_id IS NULL
            """
        )

        conn.commit()
        print("Database update complete.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
