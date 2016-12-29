import socket
import tkinter as tk
from codes import *

MAX_RECV_LEN = 4096

class ChatRoom():
    def __init__(self, host=None, quest=None):
        # init tk window
        self.host = host
        self.guest = guest
        self.root = tk.Tk()
        self.root.title(guest)

        # add elements in the window
        self.chatbox = tk.Text(self.root)
        self.msgbar = tk.Entry(self.root)
        self.button = tk.Button(self.root, text='File')

        # TODO arrange the elements


    def start(self, sock):
        self.chatbox.pack()
        self.msgbar.pack()
        self.button.pack()

        self.msgbar.bind('<Return>', send_msg(self, sock))
        self.button.bind('<Button-1>', req_file(self, sock))
        win.after(10000, poll_msg(self, sock))
        win.mainloop()

    def print(self, msg, end='\n'):
        self.chatbox.insert(END, msg+end)

def poll_msg(chatroom, sock):
    def poll():
        chatroom.chatbox.insert(END, 'Polling msg...\n')
        server_msg = sock.recv(MAX_RECV_LEN)
        while( server_msg[0] != SERVER_CODE['req_end']):
            if server_msg[0] == SERVER_CODE['transfer']:
                filename = server_msg[1:].decode()
                simpledialog.askstring('file from %s'%sender,)
                # TODO new thread to recv file

            chatroom.print(server_msg[1:].decode())
            server_msg = sock.recv(MAX_RECV_LEN)
        chatroom.print(server_msg[1:].decode())
    return poll

def send_msg(chatroom, sock):
    def send(e):
        msg = chatroom.msgbar.get()
        sock.send( MSG_REQUEST + msg.encode() )
        chatroom.msgbar.delete(0, END)
        chatroom.print(msg)
    return send

def file_recver(port):
    def recver():
        # TODO call 立人's code
        return
    return recver

def file_sender(ip, port):
    def sender():
        # TODO call 立人's code
        return
    return sender

def req_file(chatroom, filename):
    def req():
        # TODO what'd be done when one press file transfer button
        return
    return req

