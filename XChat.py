import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, simpledialog, messagebox
import sqlite3
from plyer import notification
import threading
import time

def init_db():
    with sqlite3.connect('xchat.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        status TEXT DEFAULT 'offline',
                        color TEXT DEFAULT '#FFFFFF'
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY,
                        sender TEXT NOT NULL,
                        receiver TEXT NOT NULL,
                        message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS groups (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS group_members (
                        id INTEGER PRIMARY KEY,
                        group_id INTEGER,
                        username TEXT,
                        FOREIGN KEY (group_id) REFERENCES groups (id),
                        FOREIGN KEY (username) REFERENCES users (username)
                    )''')
        conn.commit()

def update_db_schema():
    with sqlite3.connect('xchat.db') as conn:
        c = conn.cursor()
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        if 'status' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'offline'")
            conn.commit()

init_db()
update_db_schema()

class XChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XChat")
        self.root.geometry("800x600")
        self.root.configure(bg='#303030')

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_widgets()

    def create_widgets(self):
        self.frame = ctk.CTkFrame(self.root, corner_radius=10, bg_color='#303030')
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.username_label = ctk.CTkLabel(self.frame, text="Username", text_color="white")
        self.username_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.username_entry = ctk.CTkEntry(self.frame, placeholder_text="Enter username")
        self.username_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.password_label = ctk.CTkLabel(self.frame, text="Password", text_color="white")
        self.password_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.password_entry = ctk.CTkEntry(self.frame, placeholder_text="Enter password", show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.login_button = ctk.CTkButton(self.frame, text="Login", command=self.login, width=100)
        self.login_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.signup_button = ctk.CTkButton(self.frame, text="Sign Up", command=self.sign_up, width=100)
        self.signup_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.status_label = ctk.CTkLabel(self.frame, text="Status", text_color="white")
        self.status_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.status_var = tk.StringVar(value="offline")
        self.status_menu = ctk.CTkOptionMenu(self.frame, variable=self.status_var, values=["online", "offline", "dnd"])
        self.status_menu.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and Password are required")
            return

        with sqlite3.connect('xchat.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()
            if user:
                self.username = username
                self.status = self.status_var.get()
                self.update_status(username, self.status)
                self.open_chat_window()
            else:
                messagebox.showerror("Error", "Invalid Username or Password")

    def sign_up(self):
        username = simpledialog.askstring("Sign Up", "Enter username:")
        password = simpledialog.askstring("Sign Up", "Enter password:", show="*")
        if username and password:
            with sqlite3.connect('xchat.db') as conn:
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    conn.commit()
                    messagebox.showinfo("Sign Up", "User created successfully! Please log in.")
                except sqlite3.IntegrityError:
                    messagebox.showerror("Sign Up", "Username already exists.")

    def update_status(self, username, status):
        with sqlite3.connect('xchat.db') as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET status = ? WHERE username = ?", (status, username))
            conn.commit()

    def open_chat_window(self):
        self.frame.pack_forget()
        self.chat_window = ChatWindow(self.root, self.username)

class ChatWindow:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title("XChat - Chat Window")
        self.root.geometry("800x600")

        self.frame = ctk.CTkFrame(root, corner_radius=10, bg_color='#303030')
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.chat_display = ctk.CTkTextbox(self.frame, wrap=tk.WORD, height=400, state=tk.DISABLED, font=("Courier", 12))
        self.chat_display.pack(padx=10, pady=10, fill="both", expand=True)

        self.message_entry = ctk.CTkEntry(self.frame, placeholder_text="Type a message")
        self.message_entry.pack(side=tk.LEFT, padx=10, pady=10, fill="x", expand=True)

        self.send_button = ctk.CTkButton(self.frame, text="Send", command=self.send_message, width=80)
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=10)

        self.status_button = ctk.CTkButton(self.frame, text="Status", command=self.change_status, width=80)
        self.status_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.create_group_button = ctk.CTkButton(self.frame, text="Create Group", command=self.create_group, width=100)
        self.create_group_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.group_button = ctk.CTkButton(self.frame, text="Join Group", command=self.join_group, width=100)
        self.group_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Using after() to periodically check for new messages
        self.update_chat()

    def send_message(self):
        message = self.message_entry.get()
        if message:
            with sqlite3.connect('xchat.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                          (self.username, 'public', message))
                conn.commit()
            self.message_entry.delete(0, tk.END)
            self.check_and_notify()

    def change_status(self):
        status = simpledialog.askstring("Change Status", "Enter new status (e.g., online, offline, dnd):")
        if status:
            self.update_status(self.username, status)

    def create_group(self):
        group_name = simpledialog.askstring("Create Group", "Enter group name:")
        if group_name:
            with sqlite3.connect('xchat.db') as conn:
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
                    conn.commit()
                    messagebox.showinfo("Create Group", f"Group '{group_name}' created!")
                except sqlite3.IntegrityError:
                    messagebox.showerror("Create Group", "Group already exists.")

    def join_group(self):
        group_name = simpledialog.askstring("Join Group", "Enter group name:")
        if group_name:
            with sqlite3.connect('xchat.db') as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
                group = c.fetchone()
                if group:
                    group_id = group[0]
                    c.execute("INSERT INTO group_members (group_id, username) VALUES (?, ?)", (group_id, self.username))
                    conn.commit()
                    messagebox.showinfo("Join Group", f"Joined group '{group_name}'!")
                else:
                    messagebox.showerror("Join Group", "Group not found.")

    def update_chat(self):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        with sqlite3.connect('xchat.db') as conn:
            c = conn.cursor()
            c.execute("SELECT sender, message FROM messages WHERE receiver = 'public' OR receiver = ?", (self.username,))
            messages = c.fetchall()
            for sender, message in messages:
                self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.configure(state=tk.DISABLED)
        self.root.after(1000, self.update_chat)  # Update every second

    def check_and_notify(self):
        with sqlite3.connect('xchat.db') as conn:
            c = conn.cursor()
            c.execute("SELECT status FROM users WHERE username = ?", (self.username,))
            status = c.fetchone()[0]
            if status == 'online':
                self.notify("New message received!")

    def notify(self, message):
        notification.notify(
            title="XChat Notification",
            message=message,
            timeout=10
        )

if __name__ == "__main__":
    root = ctk.CTk()
    app = XChatApp(root)
    root.mainloop()
