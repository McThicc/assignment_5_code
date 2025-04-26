import threading
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST
import struct
import tkinter as tk
from tkinter import messagebox, scrolledtext, PhotoImage, simpledialog
import platform

class BidirectionalChat:

    #A rather nice font really
    default_font = ("Verdana", 16)
    background_color = "#F0F8FF"

    #The stuff for making the dang thing work and some intial states of variables I modify later
    def __init__(self, root):
        self.root = root
        self.username = ""
        self.conn = None
        self.client_socket = None
        self.connected = False
        self.udp_socket = None

        self.show_connect_screen()
    
    #The GUI for the login screen to enter your username, listening and target ports, and destination IP address
    def show_connect_screen(self):
        self.clear_root()
        self.username = tk.StringVar()
        self.listen_port = tk.StringVar(value="14142")
        self.target_ip = tk.StringVar()
        self.target_port = tk.StringVar(value="14142")

        self.root.config(bg=self.background_color)
        self.root.option_add("*Font", self.default_font)
        self.root.option_add("*Foreground", "#000080")

        tk.Label(self.root, text="Enter your username:", bg=self.background_color).pack()
        tk.Entry(self.root, textvariable=self.username, bg="white").pack()
        tk.Label(self.root, text="Enter listening port:", bg=self.background_color).pack()
        tk.Entry(self.root, textvariable=self.listen_port, bg="white").pack()
        tk.Label(self.root, text="Enter target IP:", bg=self.background_color).pack()
        tk.Entry(self.root, textvariable=self.target_ip, bg="white").pack()
        tk.Label(self.root, text="Enter target port:", bg=self.background_color).pack()
        tk.Entry(self.root, textvariable=self.target_port, bg="white").pack()

        tk.Button(self.root, text="Connect", command=self.start_chat, bg="pink").pack(pady=10)

        self.broadcast_mode = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Enable UDP Broadcast Mode", variable=self.broadcast_mode, bg=self.background_color).pack()
        tk.Button(self.root, text="Listen for UDP Broadcasts Only", command=self.start_udp_listen_only, bg=self.background_color).pack(pady=10)


    #The taking of the login info to start the processes of creating a connection
    #Shows loading screen
    def start_chat(self):
        try:
            self.username = self.username.get()
            self.listen_port = int(self.listen_port.get())
            self.target_port = int(self.target_port.get())

            self.listen_port_udp = self.listen_port + 1
            self.target_port_udp = self.target_port + 1

            if self.broadcast_mode.get():
                threading.Thread(target=self.listen_udp_broadcasts, daemon=True).start()
                self.show_chat_screen()
            else:
                self.target_ip = self.target_ip.get()
                threading.Thread(target=self.receive_messages, daemon=True).start()
                self.show_loading_screen()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    #Displays the loading screen and attempts connection
    def show_loading_screen(self):
        self.clear_root()
        self.root.config(bg="lightblue")

        tk.Label(self.root, text="Connecting...", font=("Verdana", 16), bg="lightblue").pack(pady=30)
        self.status_label = tk.Label(self.root, text="", font=("Verdana", 12), bg="lightblue")
        self.status_label.pack(pady=10)

        threading.Thread(target=self.connect_client_socket, daemon=True).start()

    #The chat screen GUI
    def show_chat_screen(self):
        self.clear_root()

        self.root.config(bg="lightblue")
        self.root.option_add("*Foreground", "green")
        self.chat_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled')
        self.chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(self.root, state='normal')
        self.msg_entry.pack(side=tk.LEFT, padx=(10, 5), pady=10, fill=tk.X, expand=True)
        print(f"msg_entry state: {self.msg_entry['state']}")

        #Only shows the send button if UDP broadcast mode was disabled
        if not self.broadcast_mode.get():
            self.send_btn = tk.Button(root, text="Send", bg="pink", fg="black", command=self.send_messages)
            self.send_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=10)
            self.msg_entry.bind("<Return>", self.send_messages)

        self.disconnect_btn = tk.Button(root, text="Disconnect", bg="pink", fg="black", command=self.disconnect)
        self.disconnect_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=10)

        #Only shows the broadcast button if UDP broadcast mode was enabled
        if self.broadcast_mode.get():
            self.broadcast_btn = tk.Button(root, text="Broadcast", bg="pink", fg="black", command=self.send_udp_broadcast)
            self.broadcast_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=10)
            self.msg_entry.bind("<Return>", self.send_udp_broadcast)

    #The function that appends messages to the chat log
    def append_messages(self, message):
        def _append():
            if hasattr(self, 'chat_log') and self.chat_log.winfo_exists():
                self.chat_log.configure(state="normal")
                self.chat_log.insert(tk.END, message + "\n")
                self.chat_log.configure(state="disabled")
                self.chat_log.see(tk.END)
        self.root.after(0, _append)

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
    def connect_client_socket(self, retries=5, delay=3):
        last_exception = None
        for attempt in range(retries):
            try:
                self.client_socket = socket(AF_INET, SOCK_STREAM)
                self.client_socket.connect((self.target_ip, self.target_port))
                self.connected = True
                print("Client socket set up!")
                self.root.after(0, self.show_chat_screen)
                return
            except Exception as e:
                last_exception = e
                self.connected = False
                self.update_status(f"Attempt {attempt + 1} failed")
                time.sleep(delay)
        self.root.after(0, lambda: messagebox.showerror("Connection Failed", str(last_exception)))
        self.root.after(0, self.show_connect_screen)

    def listen_udp_broadcasts(self):
        try:
            self.udp_socket = socket (AF_INET, SOCK_DGRAM)
            self.udp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.udp_socket.bind(('', self.listen_port_udp))

            print(self.listen_port_udp)
            while True:
                try:
                    data, addr = self.udp_socket.recvfrom(1024)
                    message = data.decode()
                    print(f"Received UDP broadcast: {message} from {addr}")
                    self.append_messages(f"{message}")
                except Exception as e:
                    self.append_messages(f"[UDP Broadcast Error] {e}")
                    break
        finally:
            if self.udp_socket:
                self.udp_socket.close()

    def start_udp_listen_only(self):
        try:
            listen_port = int(self.listen_port.get())
            self.listen_port_udp = listen_port + 1
            threading.Thread(target=self.listen_udp_broadcasts, daemon=True).start()
            self.show_chat_screen()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    #This does a lot and is very sketch
    def send_udp_broadcast(self, event=None):
        if not self.broadcast_mode.get():
            return
        
        msg = self.msg_entry.get()
        if msg:
            try:
                broadcast_msg = f"[{self.username} - Broadcast]: {msg}"
                udp_sender = socket(AF_INET, SOCK_DGRAM)
                udp_sender.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
                #Tries to calculate the proper broadcast address for the network. Defaults to 255.255.255.255 if it fails.
                broadcast_ip = self.get_broadcast_address()
                print(f"Broadcasting to {broadcast_ip}:{self.target_port_udp}")
                udp_sender.sendto(broadcast_msg.encode(), (broadcast_ip, self.target_port_udp))
                self.append_messages(broadcast_msg)
                self.msg_entry.delete(0, tk.END)
                udp_sender.close()
            except Exception as e:
                self.append_messages(f"Broadcast Failed :( - {e}")

    #Attempts to send a message
    #Attaches desired username to message so the other person know who you are
    def send_messages(self, event=None):
        msg = self.msg_entry.get()
        #If the user types "!quit" it will performs a disconnect the same as the button
        if msg == "!quit":
            self.disconnect()
        if msg and self.client_socket:
            if self.connected:
                try:
                    #Creates a new message with your username and desired message
                    usr_msg = f"[{self.username}]: {msg}"
                    self.client_socket.send(usr_msg.encode())
                    #Logs the messsge into your chat log as well for continuity
                    self.append_messages(f"[{self.username}]: {msg}")
                    #Clears the chat box so you can start fresh with each message
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
            #Sends a message to let the other user know that this user has disconnected
            disconnect_msg = f"[{self.username}] has disconnected."
            if self.client_socket:
                self.client_socket.send(disconnect_msg.encode())
            #Shuts down all the sockets
            if self.client_socket:
               self.client_socket.close() 
            if self.conn:
                self.conn.close()
            if self.udp_socket:
                self.udp_socket.close()
            self.connected = False
            self.append_messages("Disconnected")
            messagebox.showinfo("Disconnected!!", "You have been disconnected from the chat bozo, sorry.")
            self.show_connect_screen()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.show_connect_screen()

    #The function that gets the broadcast address of the local network
    def get_broadcast_address(self):
        try:
            temp_socket = socket(AF_INET, SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))  # Google's DNS - no data actually sent - I am using it to calculate
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()

            ip_parts = local_ip.split('.')
            ip_parts[-1] = '255'
            broadcast_ip = '.'.join(ip_parts)
            #return broadcast_ip
            return '255.255.255.255'
        except Exception as e:
            print(f"[Broadcast IP Error] {e}")
            return '255.255.255.255'  # Fallback if ^ this don't work


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
    root.geometry("550x600+650+150")

    #Creates an instance of the Bi-directional Chat App
    app = BidirectionalChat(root)
    #Starts the app
    root.mainloop()
