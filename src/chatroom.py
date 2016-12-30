#!/usr/bin/env python
import socket
import tkinter as tk
import tkinter.messagebox as tkbox
from codes import *
from threading import Thread
from time import sleep

from transfer import *

# TODO the following import should be removed
import random

MAX_RECV_LEN = 4096
class Chatroom():
    def __init__(self, fileports, host=None, guest=None):
        # init tk window
        self.host = host
        self.guest = guest
        self.root = tk.Tk()
        self.root.title(guest)
        self.alive = False
        self.fileports = fileports

        # add elements in the window
        self.chatbox = tk.Text(self.root)
        self.msgbar = tk.Entry(self.root)
        self.button = tk.Button(self.root, text='File')

        # TODO arrange the elements


    def start(self, ssock, rsock):
        self.ssock = ssock
        self.rsock = rsock

        self.chatbox.pack()
        self.msgbar.pack()
        self.button.pack()

        self.msgbar.bind('<Return>', thpack(send_msg, self))
        self.button.bind('<Button-1>', thpack(req_file, self))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        self.alive = True
        Thread(target=poll_msg(self)).start()
        Thread(target=self.root.mainloop).run()

    def print(self, msg, end='\n'):
        if type(msg) == bytes:
            msg = msg.decode()
        self.chatbox.insert('1.0', msg+end)
    def close(self): 
        chk = tkbox.askokcancel(
            'Quit',
            'Do you really want to leave the chatroom with %s?' % \
                self.guest,
        )
        if chk:
            self.alive = False 
            self.ssock.send(LEAVE_REQUEST)
            self.ssock.recv(MAX_RECV_LEN)
            self.root.destroy()
    def kill(self):
        self.alive = False
        self.msgbar.bind('<Return>', self.dead_note)
        self.button.bind('<Button-1>', self.dead_note)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
    def dead_note(self,e):
        self.print('The chatroom is not alive.')

def poll_msg(chatroom):
    def poll():
        sock = chatroom.rsock
        while chatroom.alive:
            sock.send(b'\x00')
            server_msg = sock.recv(MAX_RECV_LEN)

            if server_msg[:1] == MSG_REQUEST:
                chatroom.print(server_msg[1:])

            elif server_msg[:1] == TRANSFER_REQUEST:
                filename = server_msg[1:].decode()
                th_recvfile = Thread()
                th_recvfile.run = recv_file(chatroom, filename)
                th_recvfile.start()
            elif server_msg[:1] == LEAVE_REQUEST:
                chatroom.print('%s leave the chatroom.' % \
                    chatroom.guest)
                chatroom.kill()
            sleep(1)
    return poll


def thpack(function, *args, **kwargs):
    # pack the fuction with thread and change the input arguments
    def pack(*e):
        th = Thread(
            target = function,
            args = args,
            kwargs = kwargs,
            )
        th.start()
    return pack

def send_msg(chatroom):
    sock = chatroom.ssock
    msg = chatroom.msgbar.get()
    sock.send( MSG_REQUEST + msg.encode() )
    try:
        server_msg = sock.recv(MAX_RECV_LEN)
    except socket.timeout:
        chatroom.print('Timeout, trying to send again.')
        server_msg = sock.recv(MAX_RECV_LEN)
    if server_msg[0] == REQUEST_FIN[0]:
        chatroom.print(server_msg[1:])
        chatroom.msgbar.delete(0, tk.END)
    else:
        chatroom.print('Error, please send your message again.')
    return

if __name__ == '__main__':
    # This section is for unit test.
    # TODO Remove this as client gui part done
    from queue import Queue
    MAX_TRANS_AMT = 11
    server = ('localhost', 16666)
    rsock, ssock = socket.socket(), socket.socket()
    FILE_PORT = 16888

    #recvsock = socket.socket()
    try:
        q = Queue(MAX_TRANS_AMT)
        for i in range(MAX_TRANS_AMT):
            q.put(i + FILE_PORT)
        rsock.connect(server)
        ssock.connect(server)
        chatroom = Chatroom(
            fileports = q, 
            host = 'host', 
            guest = 'guest',
        )
        chatroom.start(
            rsock=rsock,
            ssock=ssock,
        )
    except OSError as e:
        print('Connection failed.')
        print(e)
        ssock.close()
        rsock.close()
        exit()
    finally:
        ssock.close()
        rsock.close()
