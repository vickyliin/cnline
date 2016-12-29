#!/usr/bin/env python
from codes import *
import tkinter as tk
import tkinter.messagebox as tkbox
import tkinter.filedialog as tkfile
import socket
from threading import Thread
from time import sleep
from os.path import isfile, basename
import queue

MAX_RECV_LEN = 4096
class TransferBox:
    def __init__(self, sender, recver, filename):
        # init tk window
        self.sender = sender
        self.recver = recver
        self.root = tk.Tk()
        self.root.title(filename)
        self.alive = False
        self.filename = filename

        # add elements in the window
        self.label = tk.Label(self.root, text='')

    def start(self, cond):
        # s: send, r: recv
        cond = cond[0]
        self.cond = cond
        cond_str = dict(
            s = ('Sending', self.filename, 'to %s' % self.recver),
            r = ('Receiving', self.filename, 'from %s' % self.sender)
        )

        self.label['text'] = '%s file %s %s...' % cond_str[cond] 

        self.label.pack()
        self.root.protocol("WM_DELETE_WINDOW", self.close())
        
        self.alive = True
        Thread(target=self.root.mainloop).run()

    def done(self, chatroom):
        cond_str = dict(
            s = 'sent to %s' % self.recver,
            r = 'recieved from %s' % self.sender,
        )
        chatroom.print(
            'File %s had been %s!' % \
            (self.filename, cond_str[self.cond])
        )
        if self.alive:
            self.close(1)
    def close(self, force=False): 
        def close():
            chk = True
            if not force:
                chk = tkbox.askokcancel(
                    'Cancel', 
                    'The transfer won\'t cancel' +
                    ' even though the window closed.\n' +
                    'Do you still want to close it?'
                )
            if chk:
                self.alive = False 
                self.root.destroy()
        return close

def file_recver(port, chatroom, filename):
    # filename for display, need not contain path
    def recver():
        chatroom.print(
            'Receiving file %s from %s, using port %d' % \
            (filename, chatroom.guest, port)
        )
        sleep(1) # TODO replace to call 立人's code
        chatroom.print( 'File %s received.' % filename )

        chatroom.fileports.put(port)
        return
    return recver

def file_sender(addr, chatroom, filename):
    # filename should contain path
    def sender():
        ip, port = addr.split(':')
        chatroom.print(
            'Sending file %s to %s' % \
            (basename(filename), chatroom.guest)
        )
        sleep(1) # TODO replace to call 立人's code
        chatroom.print( 'File %s sended.' % basename(filename) )
        return
    return sender

def recv_file(chatroom, filename):
    # do when recv a file request from server
    def recv():
        sender = chatroom.guest
        try:
            port = chatroom.fileports.get()
        except queue.Empty:
            chatroom.print(
                'You miss a file %s from %s ' % (filename,sender) +
                'because the MAX amount of file receive' +
                ' (%d) had been reached.' % MAX_TRANSFER_AMT
            )
            chatroom.ssock.send(TRANSFER_DENY)
            chatroom.ssock.recv(MAX_RECV_LEN)
            return

        accept = tkbox.askokcancel(
            'file from %s' % sender,
            'Do you want to accept file %s from %s?' % \
                (filename, sender)
        )
        chatroom.print('Accept:'+ str(accept))
        if accept == True:
            # send the picked port to server 
            # the server will then pass it to the sender
            chatroom.ssock.send(TRANSFER_ACCEPT + str(port).encode())
            chatroom.ssock.recv(MAX_RECV_LEN)

            file_recver(port, chatroom, filename)
        else:
            chatroom.ssock.send(TRANSFER_DENY)
            chatroom.ssock.recv(MAX_RECV_LEN)
    return recv

def req_file(chatroom):
    # do when click the file button
    def req(e):
        sock = chatroom.ssock
        filename = tkfile.askopenfilename()
        if not filename:
            # user cancel the file browser
            return
        tkbox.askokcancel(
            'File transfer',
            'Do you want to transfer file %s to %s?' % \
                (basename(filename), chatroom.guest)
        )
        sock.send(TRANSFER_REQUEST + basename(filename).encode())
        server_msg = sock.recv(MAX_RECV_LEN)
        if server_msg[:1] == TRANSFER_ACCEPT:
            addr = server_msg[1:].decode()
            th_sendfile = Thread()
            th_sendfile.run = file_sender(addr, chatroom, filename)
            th_sendfile.start()
        else:
            chatroom.print(server_msg[1:])
        
        return
    return req

