"""Local private key storage for Level 3 and Level 4 encryption.

Stores private keys in a local SQLite database so only public keys reside in MongoDB.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

DB_FILENAME = "private_keys.db"

class LocalPrivateKeyStore:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        base_path = Path(__file__).resolve().parent.parent / "data"
        base_path.mkdir(parents=True, exist_ok=True)
        self.db_path = (db_path or base_path / DB_FILENAME).resolve()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS private_keys (
                    flow_id TEXT PRIMARY KEY,
                    level INTEGER NOT NULL,
                    private_key_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_private_keys(self, flow_id: str, level: int, key_payload: Dict[str, Any]) -> None:
        payload_json = json.dumps(key_payload)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO private_keys (flow_id, level, private_key_json, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(flow_id) DO UPDATE SET
                    level = excluded.level,
                    private_key_json = excluded.private_key_json,
                    created_at = excluded.created_at
                """,
                (flow_id, level, payload_json, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def get_private_keys(self, flow_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT private_key_json FROM private_keys WHERE flow_id = ?",
                (flow_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return None

    def delete_private_keys(self, flow_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM private_keys WHERE flow_id = ?", (flow_id,))
            conn.commit()


local_private_key_store = LocalPrivateKeyStore()
