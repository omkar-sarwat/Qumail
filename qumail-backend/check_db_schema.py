"""Check database schema"""
import sqlite3

conn = sqlite3.connect('qumail.db')
cursor = conn.cursor()

print("Users table schema:")
cursor.execute('PRAGMA table_info(users)')
for row in cursor.fetchall():
    print(f"  {row}")

print("\nChecking for existing test user:")
cursor.execute("SELECT id, email, display_name FROM users WHERE email='test@example.com'")
result = cursor.fetchone()
if result:
    print(f"  Test user exists: ID={result[0]}, Email={result[1]}, Name={result[2]}")
else:
    print("  No test user found")

print("\nAll users in database:")
cursor.execute("SELECT id, email, display_name FROM users")
for row in cursor.fetchall():
    print(f"  ID={row[0]}, Email={row[1]}, Name={row[2]}")

conn.close()
