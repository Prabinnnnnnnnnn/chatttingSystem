# Chat System
# 💬 Python Chat Application with GUI & Admin Panel

A full-featured socket-based chat system built with Python, supporting user registration, private messaging, chat rooms, and a Tkinter-based GUI. Includes an administrative interface for real-time user moderation.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🚀 Features

### 💡 User Features
- 🧑‍💻 Register/Login with credentials
- 🗨️ Global chat and dynamic **chat rooms**
- 🔒 **Private messaging** between users
- 🧾 **Chat history** loading on login
- 👥 Real-time **online user list**
- 🖥️ **GUI client** built with Tkinter

### 🔧 Admin Features (via terminal)
- 👢 Kick and ❌ ban users
- 🔓 Unban users
- 📢 Broadcast system-wide messages
- 🧠 View recent messages and connected users



## 📂 Project Structure
```
chat-app/
├── client.py       # GUI client application
├── server.py       # Main server-side logic
├── init_db.py      # Initializes the SQLite database
├── users.db        # SQLite database (auto-generated)
└── README.md       # Project documentation

```

## ⚙️ Getting Started

### Prerequisites

- Python 3.8+
- Tkinter (included with most Python installations)

### Installation

```bash
git clone https://github.com/yourusername/chat-app.git
cd chat-app
python init_db.py       # Initialize the database
python server.py        # Start the server
python client.py        # Launch the GUI client

```

💡 Usage
Register or Login via the GUI.
Join or create rooms using the Join Room input.
Send private messages via dropdown user list.
Admins can use terminal commands to moderate.

🛡️ Security Notice
Passwords are stored in plaintext — this is fine for demos but not production.
Consider using bcrypt or argon2 for password hashing.
Add TLS/SSL for secure socket communication in a live deployment.

 Admin Commands
From the server console:
```bash
list users            # Show connected users
list messages         # View last 20 messages
kick <username>       # Disconnect a user
ban <username>        # Permanently block user
unban <username>      # Revoke ban
broadcast <message>   # Send admin announcement
exit                  # Exit admin panel
```
Contact
Prabin Shrestha
pravinxtha123@gmail.com



