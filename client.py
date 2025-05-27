import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import sys

# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))  # Change IP/port if needed

username = ""

# GUI Setup
chat = tk.Tk()
chat.title("Chat Client")

text_area = tk.Text(chat, state='disabled', height=20, width=50)
text_area.pack(padx=10, pady=5)

input_area = tk.Entry(chat, width=40)
input_area.pack(side=tk.LEFT, padx=(10, 0), pady=5)

send_button = tk.Button(chat, text="Send", command=lambda: send_message())
send_button.pack(side=tk.LEFT, padx=5)

# Authentication function
def auth():
    global username
    while True:
        action = simpledialog.askstring("Authentication", "Type 'register' or 'login':")
        if action not in ["register", "login"]:
            messagebox.showerror("Error", "Invalid action. Type 'register' or 'login'")
            continue

        username = simpledialog.askstring("Username", "Enter your username:")
        password = simpledialog.askstring("Password", "Enter your password:", show='*')

        credentials = json.dumps({
            "action": action,
            "username": username,
            "password": password
        })
        try:
            client.send(credentials.encode())
            response = client.recv(1024).decode()
            if response.startswith("✅"):
                messagebox.showinfo("Success", response)
                break
            else:
                messagebox.showerror("Error", response)
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
            chat.destroy()
            sys.exit()

# Function to send messages
def send_message():
    message = input_area.get()
    if message:
        if message.strip() == "/quit":
            client.send("/quit".encode())
            client.close()
            chat.quit()
            return
        full_message = f"{username}: {message}"
        client.send(full_message.encode())

        # Display your own message instantly
        text_area.config(state='normal')
        text_area.insert(tk.END, full_message + "\n")
        text_area.config(state='disabled')
        text_area.yview(tk.END)
        
        input_area.delete(0, tk.END)

# Function to receive messages
def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode()
            if not message:
                break
            text_area.config(state='normal')
            text_area.insert(tk.END, message + "\n")
            text_area.config(state='disabled')
            text_area.yview(tk.END)
        except:
            break

# Start client
auth()
threading.Thread(target=receive_messages, daemon=True).start()
chat.protocol("WM_DELETE_WINDOW", lambda: client.send("/quit".encode()) or client.close() or chat.destroy())
chat.mainloop()
