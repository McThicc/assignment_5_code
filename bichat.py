import threading
import sys
import datetime
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import tkinter as tk
from tkinter import messagebox, scrolledtext, PhotoImage, simpledialog
import platform

class BidirectionalChat:

    #A rather nice font really
    default_font = ("Verdana", 12)

    #The stuff for making the dang thing work and some intial states of variables I modify later
    def __init__(self, root):
        self.root = root
        self.username = ""
        self.conn = None
        self.client_socket = None
        self.connected = False

        self.show_connect_screen()
    
    #The GUI for the login screen to enter your username, listening and target ports, and destination IP address
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

        tk.Button(self.root, text="Connect", command=self.start_chat, bg="pink").pack(pady=10)
    

    #The taking of the login info to start the processes of creating a connection
    #Shows loading screen
    def start_chat(self):
        try:
            self.username = self.username.get()
            self.listen_port = int(self.listen_port.get())
            self.target_ip = self.target_ip.get()
            self.target_port = int(self.target_port.get())
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.show_loading_screen()
        except Exception as e:
            messagebox.showerror(f"Error: {e}")

    #Displays the loading screen and attempts connection
    def show_loading_screen(self):
        self.clear_root()
        self.root.config(bg="lightblue")

        tk.Label(self.root, text="Connecting...", font=("Verdana", 16), bg="lightblue").pack(pady=30)
        self.status_label = tk.Label(self.root, text="", font=("Verdana", 12), bg="lightblue")
        self.status_label.pack(pady=10)

        threading.Thread(target=self.attempt_connection, daemon=True).start()

    #The chat screen GUI
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


    #The function that appends messages to the chat log
    def append_messages(self, message):
        self.chat_log.configure(state="normal")
        self.chat_log.insert(tk.END, message + "\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.yview(tk.END)

    #Sets up the server socket and handles the recieving of the client's message
    def receive_messages(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('', self.listen_port))
        server_socket.listen(1)
        print(f"[Receiver] Listening on port {self.listen_port}...")

        self.conn, addr = server_socket.accept()
        print(f"[Receiver] Connection from {addr}")

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
    
    #Sets up the client socket for sending to the other server
    def connect_client_socket(self):
        try:
            self.client_socket = socket(AF_INET, SOCK_STREAM)
            self.client_socket.connect((self.target_ip, self.target_port))
            self.connected = True
                
            self.root.after(0, self.show_chat_screen)
        except Exception as e:
            self.append_messages(f"[Sender] Could not connect: {e}")
            self.connected = False
            self.update_status("Connection Failed, You Suck!!!")

    #Attempts to send a message
    #Attaches desired username to message so the other person know who you are
    #Logs the messsge into your chat log as well for continuity
    #Clears the chat box so you can start fresh with each message
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

    #Tiny little baby function with the power to wipe creation away
    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    #Might get rid of this if im feelin it but it gives status messages
    def update_status(self, status_message):
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.config(text=status_message)

    #The function that gets called when the disconnect button is pressed
    #Closes both sockets and displays a disconnect message before returning the user to the login screen
    def disconnect(self):
        try:
            if self.client_socket:
               self.client_socket.close() 
            if self.conn:
                self.conn.close()
            self.connected = False
            self.append_messages("Disconnected")
            messagebox.showinfo("Disconnected!!", "You have been disconnected from the chat bozo, sorry.")
            self.show_connect_screen()
        except Exception as e:
            messagebox.showerror(f"Error: {e}")

    def attempt_connection(self):
        try:
            self.client_socket = socket(AF_INET, SOCK_STREAM)
            self.client_socket.connect((self.target_ip, self.target_port))
            self.connected = True
            self.root.after(0, self.show_chat_screen)
        except Exception as e:
            self.connected = False
            self.root.after(0, lambda: messagebox.showerror("Connection Failed", str(e)))
            self.root.after(0, self.show_connect_screen)

# Main Script that makes the thing work
if __name__ == "__main__":

    #Initializes the frame for the GUI
    root = tk.Tk()
    root.title("Bi-directional Chat")

    #Sets the icon to my wonderful cat, Vinny
    #Support for both Windows and MacOS/Linux so everyone can see my cat
    system = platform.system()
    if system == "Windows":
        root.iconbitmap("vinny_icon.ico")
    else:
        icon = PhotoImage(file="vinny_image.png")
        root.iconphoto(True, icon)

    #Scale of app, change as desired
    root.geometry("400x400+650+150")

    #Creates an instance of the Bi-directional Chat App
    app = BidirectionalChat(root)
    #Starts the app
    root.mainloop()
