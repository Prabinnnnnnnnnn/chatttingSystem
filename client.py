import socket
import threading
import sys

# Connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

# Ask username for the users
username = input("Enter your name : ")
client.send(username.encode('utf-8'))

# Function to receive messages from the server
def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            print(message)
        except:
            print("[!] Connection to the server lost....")
            client.close()
            break

# Function to send messages from the server
def send_messages():
    while True:
        message = input()
        if message.lower() == "/quit":
            client.send("/quit".encode('utf-8'))
            print("👋 Exiting the chat")
            client.close()
            sys.exit()
        client.send(f"{username} : {message}".encode('utf-8'))

threading.Thread(target=receive_messages).start()
threading.Thread(target=send_messages).start()
