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
client_rooms = {}
clients_lock = threading.Lock()

def broadcast_room_user_list(room_name):
    with clients_lock:
        # Get users in the specified room
        users_in_room = [uname for client, uname in clients.items() if client_rooms.get(client) == room_name]
        user_list_json = json.dumps({"type": "room_user_list", "room": room_name, "users": users_in_room})

        for client, uname in clients.items():
            if client_rooms.get(client) == room_name:
                try:
                    client.send(f"ROOM_USER_LIST:{user_list_json}\n".encode('utf-8'))
                except:
                    del clients[client]
                    client.close()


def broadcast_room_message(room_name, message, exclude_client=None):
    with clients_lock:
        for client, uname in clients.items():
            if client != exclude_client and client_rooms.get(client) == room_name:
                try:
                    client.send(f"{message}\n".encode('utf-8'))
                except:
                    del clients[client]
                    client.close()


def join_room(client_socket, username, room_name):
    # Create room if not exists
    cursor.execute("INSERT OR IGNORE INTO rooms (room_name) VALUES (?)", (room_name,))
    conn.commit()

    # Set client current room
    client_rooms[client_socket] = room_name

    # Notify user
    client_socket.send(f"✅ You joined room '{room_name}'\n".encode())

    # Broadcast to room that user joined
    broadcast_room_message(room_name, f"🟢 {username} joined the room.", exclude_client=client_socket)
    broadcast_room_user_list(room_name)

def leave_room(client_socket, username):
    room_name = client_rooms.get(client_socket)
    if room_name:
        broadcast_room_message(room_name, f"🔴 {username} left the room.", exclude_client=client_socket)
        client_rooms[client_socket] = None
        client_socket.send("✅ You left the room. You are now in global chat.\n".encode())

        broadcast_room_user_list(room_name)

def list_rooms(client_socket):
    cursor.execute("SELECT room_name FROM rooms")
    rooms = cursor.fetchall()
    if rooms:
        rooms_list = ', '.join([r[0] for r in rooms])
        client_socket.send(f"Available rooms: {rooms_list}\n".encode())
    else:
        client_socket.send("No rooms available.\n".encode())

def handle_client(client_socket, addr):
    username = handle_auth(client_socket)
    if not username:
        try:
            client_socket.close()
        except:
            pass
        return

    with clients_lock:
        clients[client_socket] = username
    print(f"[+] New connection from {addr}")

    broadcast_message(f"🟢 {username} joined the chat", exclude_client=client_socket)
    broadcast_user_list()

    # Set default room as None or global chat
    client_rooms[client_socket] = None

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            message = message.strip()

            # Handle quit
            if message == "/quit":
                break

            # Handle list users command (existing)
            if message == "/users":
                continue

            # Room commands integration
            if message.startswith("/join "):
                room_name = message.split(" ", 1)[1].strip()
                join_room(client_socket, username, room_name)
                broadcast_room_user_list(room_name)
                continue

            elif message == "/leave":
                leave_room(client_socket, username)
                current_room = client_rooms.get(client_socket)
                if current_room:
                    broadcast_room_user_list(current_room)
                else:
                    broadcast_user_list()
                continue

            elif message == "/listrooms":
                list_rooms(client_socket)
                continue

            # Private message (existing)
            if message.startswith("/pm "):
                try:
                    _, rest = message.split(" ", 1)
                    recipient_name, private_msg = rest.strip().split(" ", 1)
                    found = False
                    with clients_lock:
                        for client, uname in clients.items():
                            if uname == recipient_name:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                formatted = f"[{timestamp}] (Private) {username} to {recipient_name}: {private_msg}"

                                try:
                                    client.send((formatted + "\n").encode())
                                except Exception as e:
                                    print(f"Error sending PM to {recipient_name}: {e}")

                                try:
                                    client_socket.send((formatted + "\n").encode())
                                except Exception as e:
                                    print(f"Error sending PM echo to sender {username}: {e}")

                                try:
                                    cursor.execute(
                                        "INSERT INTO messages (username, recipient, timestamp, message) VALUES (?, ?, ?, ?)",
                                        (username, recipient_name, timestamp, private_msg)
                                    )
                                    conn.commit()
                                except Exception as e:
                                    print(f"Error saving PM to DB: {e}")

                                found = True
                                break

                    if not found:
                        try:
                            client_socket.send(f"❌ User '{recipient_name}' not found or offline.\n".encode())
                        except Exception as e:
                            print(f"Error notifying sender user not found: {e}")

                except ValueError:
                    try:
                        client_socket.send("❌ Invalid format. Use: /pm <username> <message>\n".encode())
                    except Exception as e:
                        print(f"Error sending invalid format message: {e}")
                continue

            # Normal messages: broadcast based on room membership
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {username}: {message}"
            print(f"[{addr}] {formatted_message}")

            current_room = client_rooms.get(client_socket)
            if current_room:
                broadcast_room_message(current_room, formatted_message, exclude_client=None)
            else:
                broadcast_message(formatted_message, exclude_client=None)

        except Exception as e:
            print(f"Error in client loop for {addr}: {e}")
            break

    print(f"[-] Connection closed from {addr}")
    with clients_lock:
        if client_socket in clients:
            del clients[client_socket]
        if client_socket in client_rooms:
            room = client_rooms[client_socket]
            if room:
                broadcast_room_message(room, f"🔴 {username} left the room.", exclude_client=client_socket)
            del client_rooms[client_socket]

    try:
        client_socket.close()
    except:
        pass

    broadcast_message(f"🔴 {username} left the chat")
    broadcast_user_list()




def broadcast_message(message, room=None, exclude_client=None):
    try:
        # Save messages only if they are normal chat messages with timestamp and username
        if message.startswith("[") and ":" in message:
            parts = message.split("] ", 1)
            if len(parts) == 2:
                timestamp = parts[0][1:]
                user_and_text = parts[1].split(": ", 1)
                if len(user_and_text) == 2:
                    username = user_and_text[0].strip()
                    text = user_and_text[1].strip()
                    cursor.execute(
                        "INSERT INTO messages (username, timestamp, message) VALUES (?, ?, ?)",
                        (username, timestamp, text)
                    )
                    conn.commit()
    except Exception as e:
        print("Error saving message to database", e)

    with clients_lock:
        for client in list(clients.keys()):
            if room:
                if client_rooms.get(client) != room:
                    continue

            if client != exclude_client:
                try:
                    client.send(f"{message}\n".encode('utf-8'))
                except Exception as e:
                    print(f"Error sending message to client: {e}")
                    del clients[client]
                    if client in client_rooms:
                        del client_rooms[client]
                    try:
                        client.close()
                    except:
                        pass


                    
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
                broadcast_user_list()
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
