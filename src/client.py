#!/usr/bin/env python3
import socket
import config
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
    while( server_msg[0] != config.SERVER_CODE['req_end']):
        print('(Server#%d)'%server_msg[0], end=' ')
        print(server_msg[1:].decode())
        for (req, state) in state_transfer_dict.items():
            if server_msg[0] == config.SERVER_CODE[req]:
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
        sock.connect((config.SERVER_IP, config.PORT))
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
                        bytes([config.REQUEST_CODE['login']]) +
                        username.encode()
                    )
                elif usrcmd.startswith(cmds[1]):
                    # register
                    sock.send(bytes([config.REQUEST_CODE['register']]))
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
                    talk_req = bytes([config.REQUEST_CODE['talk']]) + guest.encode()
                    sock.send(talk_req)
                elif usrcmd.startswith(cmds[1]):
                    # logout
                    sock.send(bytes([config.REQUEST_CODE['logout']]))
                elif usrcmd.startswith(cmds[2]):
                    # exit
                    print('Goodbye!')
                    break
                elif usrcmd.startswith(cmds[3]):
                    # list online users
                    sock.send(bytes([config.REQUEST_CODE['ls']]))
                else:
                    cmd_not_found(cmds)
                    continue
                state = state_handler(sock, usrcmd, state)

            elif state == 'talk':
                cmds = ['/leave', '/transfer']
                if usrcmd.startswith(cmds[0]):
                    # leave 
                    chk = input('Do you really wanna leave the talk [y/N] ? ')
                    if not chk in ['y','Y']:
                        continue
                    sock.send(bytes([config.REQUEST_CODE['leave']]))

                elif usrcmd.startswith(cmds[1]):
                    # file transfer
                    if usrcmd[len(cmds[1]):] == '':
                        filename = input('Please enter the file name\n> ')
                    while not isfile(filename):
                        filename = input('File %s not found, please enter again or enter /cancel to cancel\n> ' % filename)
                        if filename == '/cancel':
                            break
                    if filename == '/cancel':
                        continue
                    sock.send(
                        bytes([config.REQUEST_CODE['transfer']])+
                        filename.encode()
                    )
                else:
                    sock.send(
                        bytes([config.REQUEST_CODE['msg']])+
                        usrsmd.encode()
                    )

                state = state_handler(sock, usrcmd, state)
                
    except OSError:
        print('Connection failed.')
    except KeyboardInterrupt:
        sock.close()
    finally:
        sock.close()
