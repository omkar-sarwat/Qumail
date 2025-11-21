import sqlite3

conn = sqlite3.connect('./qumail.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(key_usage)')
rows = cursor.fetchall()

print(f'Total columns: {len(rows)}\n')
print('All columns:')
for row in rows:
    col_id, name, col_type, notnull, default, pk = row
    print(f"  {col_id}: {name} ({col_type}) - NOT NULL: {bool(notnull)}, PK: {bool(pk)}")

conn.close()
