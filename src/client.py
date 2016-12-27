#!/usr/bin/env python3
import socket
import config

RECV_MSG_LEN = 4096

def login(sock, username):
    if username == '':
        username = input("Username: ")
    login_req = b'\2' + username.encode()

    server_msg = b'\0'
    login_succeed = False
    while( server_msg[0] != config.SERVER_CODE['req_end']):
        sock.send(login_req)
        server_msg = sock.recv(RECV_MSG_LEN)
        print(server_msg)
        if server_msg[0] == 1:
            login_succeed = True
            break
    if login_succeed:
        print('Welcome %s, please enter a command' % username)

    return login_succeed 

def register(sock):
    sock.send(b'\1')
    server_msg = sock.recv(RECV_MSG_LEN)
    return 0

def talk(sock, username):
    return 0

def message_exchange():
    return 0


if __name__ == '__main__':
    print('Welcome to CNLINE! Connecting to server...')
    sock = socket.socket()
    try:
        sock.connect((config.SERVER_IP, config.PORT))
        print('Connection established, please enter a command')
        state = 'start'
        while(True):
            print('> ', end='', flush='True')
            usrcmd = input()
            if state == 'start':
                cmds = ['login', 'register', 'exit']
                if usrcmd.startswith(cmds[0]):
                    # login
                    username = usrcmd[len(cmds[0]):].strip()
                    if login(sock, username):
                        state = 'login'
                elif usrcmd.startswith(cmds[1]):
                    # register
                    register(sock)
                elif usrcmd.startswith(cmds[2]):
                    # exit
                    print('Goodbye!')
                    break
                else:
                    print('Unrecognizable command! Please enter one of the following commands:')
                    for cmd in cmds:
                        print(cmd, end=" / ")
                    print()

            elif state == 'login':
                cmds = ['talk', 'logout', 'exit']
                if usrcmd.startswith(cmds[0]):
                    # talk
                    guest = usrcmd[len(cmds[0]):].strip()
                    talk(sock, guest)
                    state = 'talk'
                elif usrcmd.startswith(cmds[1]):
                    # logout
                    # TODO maybe send some request to server for logout
                    state = 'start'
                elif usrcmd.startswith(cmds[2]):
                    # exit
                    print('Goodbye!')
                    break
                else:
                    print('Unrecognizable command! Please enter one of the following commands:')
                    for cmd in cmds:
                        print(cmd, end=" / ")
                    print()

            elif state == 'talk':
                cmds = ['/exit', '/transfer']
                if usercmd.startswith(cmds[0]):
                    # exit
                    chk_exit = input('Do you really want to exit the talk[y/N]?')
                    if chk_exit in ['n','N']:
                        state = 'login'
                        print('Exit the talk. Please enter a command to continue')
                elif usercmd.startswith(cmds[1]):
                    # file transfer
                    file_transfer()
                else:
                    message_exchange()
                
    except OSError:
        print('Connection failed.')
    else:
        sock.shutdown(socket.SHUT_WR)
