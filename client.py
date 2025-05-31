import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import sys
from datetime import datetime


# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))  # Change IP/port if needed

username = ""

# GUI Setup
chat = tk.Tk()
chat.geometry("700x500")
main_frame = tk.Frame(chat)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

chat_frame = tk.Frame(main_frame)
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

text_frame = tk.Frame(chat_frame)
text_frame.pack(fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

text_area = tk.Text(text_frame, state='disabled', height=20, width=50, yscrollcommand=scrollbar.set)
text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=text_area.yview)

input_frame = tk.Frame(chat_frame)
input_frame.pack(fill=tk.X, pady=(5, 0))

input_area = tk.Entry(input_frame, width=40)
input_area.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

send_button = tk.Button(input_frame, text="Send", command=lambda: send_message())
send_button.pack(side=tk.RIGHT)

# User list panel
user_frame = tk.Frame(main_frame, width=150)
user_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
user_frame.pack_propagate(False)

user_label = tk.Label(user_frame, text="Online Users", font=("Arial", 10, "bold"))
user_label.pack(pady=(0, 5))

user_list_frame = tk.Frame(user_frame)
user_list_frame.pack(fill=tk.BOTH, expand=True)

user_scrollbar = tk.Scrollbar(user_list_frame)
user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

user_listbox = tk.Listbox(user_list_frame, yscrollcommand=user_scrollbar.set, font=("Arial", 9))
user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
user_scrollbar.config(command=user_listbox.yview)


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
                chat.title(f"Chat client -{username}")
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
        
        client.send(message.encode())  # Just send raw message
        input_area.delete(0, tk.END)   # Clear input field

def update_user_list(users):
    user_listbox.delete(0, tk.END)
    for user in users:
        user_listbox.insert(tk.END, f"🟢 {user}")



def display_chat_message(line):
    def update():
        text_area.config(state = 'normal')
        text_area.insert(tk.END, line + "\n")
        text_area.config(state='disabled')
        text_area.yview(tk.END)
    chat.after(0,update)


# Function to receive messages
def receive_messages():
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            if not data:
                break
            
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("USER_LIST:"):
                    try:
                        user_data = json.loads(line[10:])
                       
                        if user_data["type"] == "user_list":
                            update_user_list(user_data["users"])
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON decode error: {e}")
                else:
                    display_chat_message(line)

        except Exception as e:
            print(f"Error receiving message: {e}")
            break


# Start client
auth()
threading.Thread(target=receive_messages, daemon=True).start()
chat.protocol("WM_DELETE_WINDOW", lambda: client.send("/quit".encode()) or client.close() or chat.destroy())
def on_enter(event):
    send_message()

input_area.bind('<Return>', on_enter)
chat.mainloop()
