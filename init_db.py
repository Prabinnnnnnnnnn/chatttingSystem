import sqlite3
import os

# Get absolute path to see where the DB is created
db_path = os.path.abspath("users.db")
print(f"Creating database at: {db_path}")

# Connect to SQLite database (will create if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')

# Create messages table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        message TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print(" Database and tables initialized successfully.")
