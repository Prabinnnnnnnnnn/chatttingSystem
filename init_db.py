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
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user', is_admin INTEGER DEFAULT 0, banned INTEGER DEFAULT 0
    )
''')

# Create messages table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        recipient TEXT,
        timestamp TEXT NOT NULL,
        message TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username)
    )
''')
# Create rooms table
cursor.execute("""
CREATE TABLE IF NOT EXISTS rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT UNIQUE NOT NULL
)
""")

# Create room_messages table
cursor.execute("""
CREATE TABLE IF NOT EXISTS room_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (username) REFERENCES users(username)
)
""")

conn.commit()
conn.close()

print(" Database and tables initialized successfully.")
