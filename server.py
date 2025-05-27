import socket
import threading

# Creating a server object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a public host and port
server.bind(('0.0.0.0', 5555))

# Start listening for the connections
server.listen()
print("[*] Server listening on the port 5555 ....")

clients = []

def handle_client(client_socket, addr):
    print(f"[+] New connection from {addr}")

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message: 
                break

            print(f"[{addr}] {message}")
            broadcast(message, client_socket)
        except:
            break
    print(f"[-] Connection closed from {addr}")
    clients.remove(client_socket)
    client_socket.close()


def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            client.send(message.encode('utf-8'))

# Main Server Loop

while True:
    client_socket, addr = server.accept()
    clients.append(client_socket)
    thread = threading.Thread(target=handle_client, args=(client_socket, addr))
    thread.start()
