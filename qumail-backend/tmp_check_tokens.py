import sqlite3

conn = sqlite3.connect('qumail.db')
cur = conn.cursor()
cur.execute("SELECT email, oauth_access_token IS NOT NULL as has_token, length(COALESCE(oauth_access_token, '')) as token_length FROM users")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
