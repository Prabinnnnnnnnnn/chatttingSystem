import socket
import threading
import sqlite3
import json
import time
from datetime import datetime

# Setup SQLite connection
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
# Creating a server object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a public host and port
server.bind(('0.0.0.0', 5555))

# Start listening for the connections
server.listen()
print("[*] Server listening on the port 5555 ....")

clients = {}
clients_lock = threading.Lock()

def handle_client(client_socket, addr):
    username = handle_auth(client_socket)
    if not username:
        client_socket.close()
        return
    with clients_lock:
         clients[client_socket] = username
    print(f"[+] New connection from {addr}")
    send_user_list(client_socket)
    broadcast_message(f"🟢 {username} joined the chat", exclude_client=client_socket)
    broadcast_user_list()

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message or message.strip() == "/quit": 
                break

            if message.strip == "/users":
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {username}: {message}"
            print(f"[{addr}] {formatted_message}")
            broadcast_message(formatted_message, exclude_client=None) 
        except:
            break
    print(f"[-] Connection closed from {addr}")
    with clients_lock:
        if client_socket in clients:
            del clients[client_socket]
    client_socket.close()
    broadcast_message(f"🔴 {username} left the chat")
    broadcast_user_list()

def broadcast_message(message, exclude_client=None):

    try:
        if message.startswith("[") and ":" in message:
            parts = message.split("] ", 1)
            if len(parts) == 2:
                timestamp = parts[0][1:]
                user_and_text = parts[1].split(": ",1)
                username = user_and_text[0].strip()
                text = user_and_text[1].strip()
                print("Messages are being saved")

                cursor.execute("INSERT INTO messages (username, timestamp, message) VALUES(?,?,?) ",(username, timestamp, text))
                conn.commit()
    except Exception as e:
        print("Error saving message to database", e)

    with clients_lock:
        for client in list(clients.keys()):
            if client != exclude_client:
                try:
                    client.send(f"{message}\n".encode('utf-8'))  # Ensure newline
                except:
                    del clients[client]
                    client.close()
                    
def broadcast_user_list():
    with clients_lock:
        user_list = list(clients.values())
        user_list_json = json.dumps({"type": "user_list", "users": user_list})
        
        for client in list(clients.keys()):
            try:
                # Send user list update with newline
                client.send(f"USER_LIST:{user_list_json}\n".encode('utf-8'))
            except:
                del clients[client]
                client.close()

def send_user_list(client_socket):
    with clients_lock:
        user_list = list(clients.values())
        user_list_json = json.dumps({"type": "user_list", "users": user_list})
        try:
            client_socket.send(f"USER_LIST:{user_list_json}".encode('utf-8'))
        except:
            pass

# Retrieve old messages to the chat

def send_old_messages(client_socket, username):
    try:
        cursor.execute("SELECT timestamp, message FROM messages WHERE username = ? ORDER BY id ASC", (username,))
        rows = cursor.fetchall()
        if rows:
            client_socket.send("\nPrevious Messages:\n".encode())
            for row in rows:
                timestamp = row[0]
                message = row[1]
                formatted = f"[{timestamp}] {username}: {message}"
                client_socket.send((formatted + "\n").encode())
        else:
            client_socket.send("No previous messages.\n".encode())
    except Exception as e:
        print("Error sending old messages:", e)
        client_socket.send("Error loading previous messages.\n".encode())


def handle_auth(client_socket):
    try:
        data = client_socket.recv(1024).decode('utf-8')
        credentials = json.loads(data)
        action = credentials['action']
        username = credentials['username']
        password = credentials['password']

        if action == 'register':
            cursor.execute("SELECT * FROM users WHERE username =?", (username,))
            if cursor.fetchone():
                client_socket.send("Username already exists".encode())
                return None
            cursor.execute("INSERT INTO users (username,password) VALUES (?,?)", (username, password))
            conn.commit()
            client_socket.send(f"✅Registered as {username}".encode())
            return username
        
        elif action == 'login':
            cursor.execute("SELECT * FROM users WHERE username =? AND password =?",(username,password))
            if cursor.fetchone():
                client_socket.send(f"✅ Logged in as {username}".encode())

                send_old_messages(client_socket, username)
                return username
            else:
                client_socket.send("Invalid credentials".encode())
                return None
        else:
            client_socket.send("Invalid action".encode())
            return None
    except Exception as e:
        print("Auth error", e)
        try:
            client_socket.send("Auth Error".encode())
        except:
            pass
        return None
            



# Main Server Loop

running = True
server.settimeout(1.0)  # Timeout every 1 second on accept()

try:
    while running:
        try:
            client_socket, addr = server.accept()
        except socket.timeout:
            # Just a timeout to allow loop to check running flag
            continue
        
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

except KeyboardInterrupt:
    print("\n[!] Server is shutting down...")
    running = False

# Clean up after exiting the loop
for client in clients:
    try:
        client.send("Server is shutting down.".encode())
        client.close()
    except:
        pass

server.close()
print("[*] Server closed cleanly.")
