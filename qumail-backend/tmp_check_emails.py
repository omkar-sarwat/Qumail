import sqlite3
import json

conn = sqlite3.connect('qumail.db')
cur = conn.cursor()
cur.execute("SELECT id, sender_email, receiver_email, subject, security_level, gmail_message_id, encryption_metadata FROM emails ORDER BY created_at DESC LIMIT 5")
rows = cur.fetchall()
for row in rows:
    id_, sender, receiver, subject, level, gmail_id, metadata = row
    print('ID:', id_)
    print('  sender:', sender)
    print('  receiver:', receiver)
    print('  subject:', subject)
    print('  level:', level)
    print('  gmail_message_id:', gmail_id)
    if metadata:
        if isinstance(metadata, bytes):
            metadata = metadata.decode()
        if isinstance(metadata, str):
            try:
                parsed = json.loads(metadata)
            except json.JSONDecodeError:
                parsed = {'raw': metadata[:80]}
        else:
            parsed = metadata
    else:
        parsed = {}
    if isinstance(parsed, dict):
        print('  metadata keys:', list(parsed.keys()))
    else:
        print('  metadata type:', type(parsed))
    print('-'*40)
conn.close()
