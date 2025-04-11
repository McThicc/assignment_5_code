import threading
import sys
import datetime
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import tkinter as tk
from tkinter import messagebox, scrolledtext, PhotoImage, simpledialog

class BidirectionalChat:

    default_font = ("Verdana", 12)

    def __init__(self, root):
        self.root = root
        root.title("Bi-directional Chat")
        self.username = ""
        self.conn = None
        self.client_socket = None
        self.connected = False

        self.show_connect_screen()
    
    def show_connect_screen(self):
        self.clear_root()
        self.username = tk.StringVar()
        self.listen_port = tk.StringVar()
        self.target_ip = tk.StringVar()
        self.target_port = tk.StringVar()

        self.root.config(bg="lightgray")
        self.root.option_add("*Font", self.default_font)

        tk.Label(self.root, text="Enter your username:", bg="lightgray").pack()
        tk.Entry(self.root, textvariable=self.username).pack()
        tk.Label(self.root, text="Enter listening port:", bg="lightgray").pack()
        tk.Entry(self.root, textvariable=self.listen_port).pack()
        tk.Label(self.root, text="Enter target IP:", bg="lightgray").pack()
        tk.Entry(self.root, textvariable=self.target_ip).pack()
        tk.Label(self.root, text="Enter target port:", bg="lightgray").pack()
        tk.Entry(self.root, textvariable=self.target_port).pack()

        tk.Button(self.root, text="Connect", command=self.start_chat).pack(pady=10)
    
    def start_chat(self):
        try:
            self.username = self.username.get()
            listen_port = int(self.listen_port.get())
            self.target_ip = self.target_ip.get()
            self.target_port = int(self.target_port.get())

            self.listen_port = listen_port
            self.show_chat_screen()

            threading.Thread(target=self.receive_messages, daemon=True).start()
            threading.Thread(target=self.connect_client_socket, daemon=True).start()
        except Exception as e:
            messagebox.showerror(f"Error: {e}")

    def show_chat_screen(self):
        self.clear_root()

        self.root.config(bg="lightblue")
        self.chat_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled')
        self.chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(root)
        self.msg_entry.pack(side=tk.LEFT, padx=(10, 5), pady=10, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_messages)

        self.send_btn = tk.Button(root, text="Send", command=self.send_messages)
        self.send_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=10)

        self.disconnect_btn = tk.Button(root, text="Disconnect", command=self.disconnect).pack()

    def append_messages(self, message):
        self.chat_log.configure(state="normal")
        self.chat_log.insert(tk.END, message + "\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.yview(tk.END)

    def receive_messages(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('', self.listen_port))
        server_socket.listen(1)
        self.append_messages(f"[Receiver] Listening on port {self.listen_port}...")

        self.conn, addr = server_socket.accept()
        self.append_messages(f"[Receiver] Connection from {addr}")

        while True:
            try:
                message = self.conn.recv(1024).decode()
                if not message:
                    break
                self.append_messages(f"{message}")
            except Exception as e:
                self.append_messages(f'An error occurred: {e}')
                break
        self.conn.close()
    
    def connect_client_socket(self):
        try:
            self.client_socket = socket(AF_INET, SOCK_STREAM)
            self.client_socket.connect((self.target_ip, self.target_port))
            self.append_messages(f"[Sender] Connected to {self.target_ip}:{self.target_port}")
            self.connected = True
        except Exception as e:
            self.append_messages(f"[Sender] Could not connect: {e}")
            self.connected = False

    def send_messages(self, event=None):
        msg = self.msg_entry.get()
        if msg and self.client_socket:
            if self.connected:
                try:
                    usr_msg = f"[{self.username}]: {msg}"
                    self.client_socket.send(usr_msg.encode())
                    self.append_messages(f"[{self.username}]: {msg}")
                    self.msg_entry.delete(0, tk.END)
                except Exception as e:
                    self.append_messages(f"Failed to send: {e}")
            else:
                self.append_messages("Not Connected!!!")

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def disconnect(self):
        global client_socket
        try:
            client_socket.close()
            messagebox.showinfo("Disconnected!!", "You have been disconnected from the chat bozo, sorry.")
        except Exception as e:
            messagebox.showerror(f"Error: {e}")
# Entry point
if __name__ == "__main__":

    root = tk.Tk()
    root.geometry("400x400+650+150")
    app = BidirectionalChat(root)
    root.mainloop()
