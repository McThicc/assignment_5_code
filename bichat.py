import threading
import sys
import datetime
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import tkinter as tk
from tkinter import messagebox, scrolledtext, PhotoImage, simpledialog

class BidirectionalChat:
    def __init__(self, root, listen_port, target_ip, target_port):
        self.root = root
        self.listen_port = listen_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.conn = None
        self.client_socket = None
        self.connected = False

        root.title("Bi-directional Chat")
        root.config(bg="pink")
        root.minsize(600, 900)
        root.maxsize(900, 900)
        root.geometry("400x400+650+150")

        self.chat_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 12))
        self.chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(root, font=("Arial", 12))
        self.msg_entry.pack(side=tk.LEFT, padx=(10, 5), pady=10, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_messages)

        self.send_btn = tk.Button(root, text="Send", command=self.send_messages, font=("Arial", 12))
        self.send_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=10)

        threading.Thread(target=self.receive_messages, daemon=True).start()
        threading.Thread(target=self.connect_client_socket, daemon=True).start()
        
    def append_messages(self, message):
        self.chat_log.configure(state="normal")
        self.chat_log.insert(tk.END, message + "\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.yview(tk.END)

    def receive_messages(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('', listen_port))
        server_socket.listen(1)
        print(f"[Receiver] Listening on port {listen_port}...")

        self.conn, addr = server_socket.accept()
        print(f"[Receiver] Connection from {addr}")

        while True:
            try:
                message = self.conn.recv(1024).decode()
                if not message:
                    break
                print(f"\n[Them]: {message}")
            except Exception as e:
                print(f'An error occurred: {e}')
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
                    self.client_socket.send(msg.encode())
                    self.append_messages(f"[You]: {msg}")
                    self.msg_entry.delete(0, tk.END)
                except Exception as e:
                    self.append_messages(f"Failed to send: {e}")
            else:
                self.append_messages("Not Connected!!!")

# Entry point
if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage: python chat_node.py  <listening_port> <target_ip> <target_port>")
        sys.exit(1)

    listen_port = int(sys.argv[1])
    target_ip = sys.argv[2]
    target_port = int(sys.argv[3])

    root = tk.Tk()
    app = BidirectionalChat(root, listen_port, target_ip, target_port)
    root.mainloop()
