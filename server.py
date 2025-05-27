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

clients = []
clients_lock = threading.Lock()

def handle_client(client_socket, addr):
    username = handle_auth(client_socket)
    if not username:
        client_socket.close()
        return
    with clients_lock:
         clients.append(client_socket)
    print(f"[+] New connection from {addr}")

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message: 
                break

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {username} : {message}"
            print(f"[{addr}] {formatted_message}")
            broadcast(formatted_message, client_socket)
        except:
            break
    print(f"[-] Connection closed from {addr}")
    clients.remove(client_socket)
    client_socket.close()

def broadcast(formatted_message, sender_socket=None):
    with clients_lock:
        for client in clients[:]:
            try:
                client.send(formatted_message.encode('utf-8'))
            except:
                clients.remove(client)
                client.close()


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
