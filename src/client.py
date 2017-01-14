#!/usr/bin/env python3
from util import *
from chatroom import *

MAX_RECV_LEN = 4096

def cmd_not_found(cmds):
    print('Unrecognized command.\nPlease enter one of the following commands:')
    for cmd in cmds:
        print(cmd, end='/ ')
    print()
    return

state_transfer_dict = {
    LOGIN_SUCCEED : 'login',
    LOGOUT_SUCCEED : 'start', 
}

def state_handler(sock, cmd, init_state):
    # recv msg from server and send back, return the resulting state
    # need to send request to server before this function called
    server_msg = sock.recv(MAX_RECV_LEN)
    code, msg = server_msg[:1], server_msg[1:]
    while( code != REQUEST_FIN):
        print('(Server#%s)' % code[0], end=' ')
        print(msg.decode())
        for (condition, state) in state_transfer_dict.items():
            if code == condition:
                return state

        if code == b'\x00':
            new_cmd = input('(%s)> '%cmd)
            if new_cmd:
                sock.send(new_cmd.encode())
            else:
                sock.send(b' ')
            server_msg = sock.recv(MAX_RECV_LEN)
            code, msg = server_msg[:1], server_msg[1:]
    print('(Server#%d)'%code[0], end=' ')
    print(msg.decode())
    return init_state

if __name__ == '__main__':
    print('Welcome to CNLINE! Connecting to server...')
    sock = socket.socket()
    try:
        sock.connect((config.SERVER_IP, config.PORT))
        print('Connection established, please enter a command.')
        state = 'start'
        while(True):
            if state == 'start':
                usrcmd = input('(%s)> '%state)
                cmds = ['login', 'register', 'exit']
                if usrcmd.startswith(cmds[0]):
                    # login
                    username = usrcmd[len(cmds[0]):].strip()
                    if username == '':
                        username = input('Username: ')
                    sock.send(LOGIN_REQUEST + username.encode())
                elif usrcmd.startswith(cmds[1]):
                    # register
                    sock.send(REGISTER_REQUEST)
                elif usrcmd.startswith(cmds[2]):
                    # exit
                    print('Goodbye!')
                    break
                else:
                    cmd_not_found(cmds)
                    continue
                state = state_handler(sock, usrcmd, state)

            elif state == 'login':
                manager = LoginManager(sock, username)
                manager.start()
                if not manager.login:
                    print('You just logged out.')
                    state = 'start'
                else:
                    print('Type anything except exit to open the window.')
                    usrcmd = input('(login)> ')
                    if usrcmd == 'exit':
                        print('Goodbye!')
                        break
    except OSError:
        print('Connection failed.')
    finally:
        sock.close()
