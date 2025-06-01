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

# PM selection frame
pm_frame = tk.Frame(user_frame)
pm_frame.pack(pady=10)

pm_label = tk.Label(pm_frame, text="Private Message To:")
pm_label.pack()

pm_target = tk.StringVar()
pm_dropdown = tk.OptionMenu(pm_frame, pm_target, "")
pm_dropdown.pack()

# --- ROOM CONTROLS ---

room_frame = tk.Frame(main_frame)
room_frame.pack(fill=tk.X, pady=(5, 10))

room_label = tk.Label(room_frame, text="Chat Rooms", font=("Arial", 10, "bold"))
room_label.pack(side=tk.LEFT)

room_entry = tk.Entry(room_frame, width=20)
room_entry.pack(side=tk.LEFT, padx=(5, 5))

join_room_btn = tk.Button(room_frame, text="Join Room", command=lambda: join_room())
join_room_btn.pack(side=tk.LEFT)

leave_room_btn = tk.Button(room_frame, text="Leave Room", command=lambda: leave_room())
leave_room_btn.pack(side=tk.LEFT, padx=(5, 0))

list_rooms_btn = tk.Button(room_frame, text="List Rooms", command=lambda: list_rooms())
list_rooms_btn.pack(side=tk.LEFT, padx=(5, 0))

current_room_var = tk.StringVar(value="Global")
current_room_label = tk.Label(room_frame, textvariable=current_room_var, fg="blue")
current_room_label.pack(side=tk.LEFT, padx=(10, 0))

def join_room():
    room = room_entry.get().strip()
    if room:
        client.send(f"/join {room}".encode())
        current_room_var.set(f"Room: {room}")

def leave_room():
    client.send("/leave".encode())
    current_room_var.set("Global")

def list_rooms():
    client.send("/list_rooms".encode())




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
    message = input_area.get().strip()
    if message:
        target = pm_target.get()
        if target and target != username:  # private message
            full_message = f"/pm {target} {message}"
        else:
            # Regular message goes to current room on server side
            full_message = message

        client.send(full_message.encode())
        input_area.delete(0, tk.END)



def update_user_list(users):
    user_listbox.delete(0, tk.END)
    
    menu = pm_dropdown["menu"]
    menu.delete(0, "end")

    for user in users:
        user_listbox.insert(tk.END, f"🟢 {user}")
        menu.add_command(label=user, command=lambda value=user: pm_target.set(value))



def display_chat_message(line):
    def update():
        text_area.config(state='normal')

        if "joined the room" in line:
            text_area.insert(tk.END, "🟢 " + line + "\n", "joinleave")
        elif "left the room" in line:
            text_area.insert(tk.END, "🔴 " + line + "\n", "joinleave")
        elif "(Private)" in line:
            text_area.insert(tk.END, "🔒 " + line + "\n", "pm")
        else:
            text_area.insert(tk.END, line + "\n")

        text_area.config(state='disabled')
        text_area.yview(tk.END)

        text_area.tag_config("pm", foreground="blue", font=("Arial", 10, "italic"))
        text_area.tag_config("joinleave", foreground="green", font=("Arial", 10, "bold"))

    chat.after(0, update)




# Function to receive messages
def receive_messages():
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            if not data:
                print("[*] Server closed connection.")
                break  # Exit loop if server closed socket
            
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
    # When loop breaks, close GUI safely
    chat.after(0, on_close)



# Start client
auth()
threading.Thread(target=receive_messages, daemon=True).start()
def on_close():
    try:
        client.send("/quit".encode())  # Tell server you're quitting
    except:
        pass
    try:
        client.close()  # Close socket
    except:
        pass
    chat.destroy()     # Close GUI
    sys.exit()         # Exit program

chat.protocol("WM_DELETE_WINDOW", on_close)

def on_enter(event):
    send_message()

input_area.bind('<Return>', on_enter)
chat.mainloop()
