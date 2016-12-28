#!/usr/bin/env python3
import socket
from config import *
from tkinter import *
from threading import Thread
from os.path import isfile

MAX_RECV_LEN = 4096

def cmd_not_found(cmds):
    print('Unrecognized command.\nPlease enter one of the following commands:')
    for cmd in cmds:
        print(cmd, end='/ ')
    print()
    return

state_transfer_dict = dict(
        login_succeed = 'login',
        talk_req_succeed = 'talk', 
        logout_succeed = 'start', 
)
def state_handler(sock, cmd, init_state):
    # recv msg from server and send back, return the resulting state
    server_msg = sock.recv(MAX_RECV_LEN)
    while( server_msg[0] != SERVER_CODE['req_end']):
        print('(Server#%d)'%server_msg[0], end=' ')
        print(server_msg[1:].decode())
        for (req, state) in state_transfer_dict.items():
            if server_msg[0] == SERVER_CODE[req]:
                return state

        if server_msg[0] == 0:
            sock.send(input('(%s)> '%cmd).encode())
            server_msg = sock.recv(MAX_RECV_LEN)
    print('(Server#%d)'%server_msg[0], end=' ')
    print(server_msg[1:].decode())
    return init_state

if __name__ == '__main__':
    print('Welcome to CNLINE! Connecting to server...')
    sock = socket.socket()
    try:
        sock.connect((SERVER_IP, PORT))
        print('Connection established, please enter a command.')
        state = 'start'
        while(True):
            usrcmd = input('(%s)> '%state)
            if state == 'start':
                cmds = ['login', 'register', 'exit']
                if usrcmd.startswith(cmds[0]):
                    # login
                    username = usrcmd[len(cmds[0]):].strip()
                    if username == '':
                        username = input('Username: ')
                    sock.send(
                        bytes([REQUEST_CODE['login']]) +
                        username.encode()
                    )
                elif usrcmd.startswith(cmds[1]):
                    # register
                    sock.send(bytes([REQUEST_CODE['register']]))
                elif usrcmd.startswith(cmds[2]):
                    # exit
                    print('Goodbye!')
                    break
                else:
                    cmd_not_found(cmds)
                    continue
                state = state_handler(sock, usrcmd, state)
                

            elif state == 'login':
                cmds = ['talk', 'logout', 'exit', 'ls']
                if usrcmd.startswith(cmds[0]):
                    # talk
                    guest = usrcmd[len(cmds[0]):].strip()
                    if guest == '':
                        guest = input('To: ')
                    talk_req = bytes([REQUEST_CODE['talk']]) + guest.encode()
                    sock.send(talk_req)
                elif usrcmd.startswith(cmds[1]):
                    # logout
                    sock.send(bytes([REQUEST_CODE['logout']]))
                elif usrcmd.startswith(cmds[2]):
                    # exit
                    print('Goodbye!')
                    break
                elif usrcmd.startswith(cmds[3]):
                    # list online users
                    sock.send(bytes([REQUEST_CODE['ls']]))
                else:
                    cmd_not_found(cmds)
                    continue
                state = state_handler(sock, usrcmd, state)

            elif state == 'talk':
                win = Tk()
                win.title(guest)
                chatbox = Text(win)
                msg_bar = Entry(win)
                msg_bar.bind('<Return>', send_msg)
                file_but = Button(win, text='File transfer')
                def send_msg(e):
                    msg = msg_bar.get()
                    chatbox.insert(END,
                        username + ': ' + msg + '\n')
                    sock.send( 
                        bytes([REQUEST_CODE['msg']]) + 
                        msg.encode() )
                
                th_poll = Thread()
                th_poll.run = msg_poll(sock)
                th_poll.start()
                

                state = 'login'
                
    except OSError:
        print('Connection failed.')
    except KeyboardInterrupt:
        sock.close()
    finally:
        sock.close()
