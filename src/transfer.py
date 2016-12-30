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

def file_recver(port, chatroom, filename):
    # filename for display, need not contain path
    chatroom.print(
        'Receiving file %s from %s, using port %d' % \
        (filename, chatroom.guest, port)
    )
    ### TODO replace to call 立人's code
    sleep(1) 
    # recv(port)
    # create a server with port=port to recv file
    # *need little modification to notify error
    ######
    chatroom.print( 'File %s received.' % filename )

    chatroom.fileports.put(port)
    return

def file_sender(addr, chatroom, filename):
    # filename should contain path
    ip, port = addr.split(':')
    chatroom.print(
        'Sending file %s to %s' % \
        (basename(filename), chatroom.guest)
    )
    ### TODO replace to call 立人's code
    sleep(1) 
    # send(ip,port,filename)
    # connect to sender with ip=ip, port=port and then
    # transfer file with filename
    # *need little modification to notify error
    ######
    chatroom.print( 'File %s sended.' % basename(filename) )
    return

def recv_file(chatroom, filename):
    # do when recv a file request from server
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
    if accept == True:
        # send the picked port to server 
        # the server will then pass it to the sender
        chatroom.ssock.send(TRANSFER_ACCEPT + str(port).encode())
        chatroom.ssock.recv(MAX_RECV_LEN)

        chatroom.print('File transfer request ACCEPTED.')
        file_recver(port, chatroom, filename)
    else:
        chatroom.ssock.send(TRANSFER_DENY)
        chatroom.ssock.recv(MAX_RECV_LEN)
        chatroom.print('File transfer request REJECTED.')

def req_file(chatroom):
    # do when click the file button
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
        file_sender(addr, chatroom, filename)
    else:
        chatroom.print(server_msg[1:])
    
    return

