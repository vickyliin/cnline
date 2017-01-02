#!/usr/bin/env python3

import sqlite3
import os
import sys
import socket
import select
from hashlib import sha256
from datetime import datetime
from codes import *
import config

class Server:
    def __init__(self, port):
        self.port = port
        self.connections = {}
        self.login_connections = {}

    def start(self):
        self.db = DBConnection()
        with socket.socket() as sock, select.epoll() as epoll:
            try:
                # bind the socket and register to epoll object
                sock.bind(("0.0.0.0", self.port))
                sock.listen(5)
                print("socket created : " + str(sock))
                epoll.register(sock.fileno(), select.EPOLLIN)

                while True:
                    for fd, event in epoll.poll():
                        # accept new connections, register to epoll
                        if fd == sock.fileno():
                            connsock, _ = sock.accept()
                            print("accept new connetion : " + str(connsock))
                            epoll.register(connsock.fileno(), select.EPOLLIN)
                            # Create connection object, store into dict
                            conn = Connection(connsock)
                            self.connections[conn.sock.fileno()] = conn
                        # handle other requests
                        elif event & select.EPOLLIN:
                            conn = self.connections[fd]
                            try:
                                handle_request(conn, self)
                            # remote socket closed
                            except socket.error as e:
                                print("connetion closed : " + str(conn.sock))
                                del self.connections[conn.sock.fileno()]
                                conn.sock.close()
            except KeyboardInterrupt:
                sock.close()
                self.db.close()
                exit()

class Connection:
    def __init__(self, sock):
        self.uid = None
        self.username = None
        self.login = False
        self.last_login = ""
        self.last_logout = ""
        self.sock = sock
        self.task = None

class DBConnection:
    def __init__(self):
        self.conn = sqlite3.connect(config.USERS_DB_PATH)
    def register(self, username, password):
        with self.conn:
            self.conn.execute('''INSERT INTO users(username, password, reg_time)
                                 VALUES(?, ?, ?)''', (
                                     username,
                                     sha256((password + config.PASSWORD_SALT).encode()).hexdigest(),
                                     datetime.utcnow().isoformat(' ')
                                ))

    def fetch_user(self, username):
        with self.conn:
            self.cur = self.conn.cursor()
            self.cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self.cur.fetchone()

    def close(self):
        self.conn.close()

def register_handler(conn, server):
    while True:
        # ask for username
        conn.sock.send(b"\x00-----Registration-----\nPlease enter you username, or /cancel to cancel :")
        yield

        username = conn.msg.decode('UTF-8')
        if username == "/cancel":
            conn.sock.send(REQUEST_FIN + b'Request canceled.')
            raise StopIteration
        # check if username already in use.
        if server.db.fetch_user(username) != None:
            conn.sock.send(b"\x00Sorry, this username is already used, please try with another.\n")
        else:
            break
    while True:
        # ask for password
        conn.sock.send(b"\x00Please enter you password:")
        yield
        password = conn.msg.decode('UTF-8')
        
        # confirm password
        conn.sock.send(b"\x00Please enter you password again:")
        yield

        password_2 = conn.msg.decode('UTF-8')

        if password == password_2:
            break
        else:
            conn.sock.send(b"\x00Two password doesn't match!!\n")

    print("%s, %s" % (username, password))
    server.db.register(username, password)
    conn.sock.send(REQUEST_FIN + b" Registration Success!")
    raise StopIteration
    
def login_handler(conn, server):
    username = conn.msg.decode('UTF-8')
    # check if username exists
    user_inf = server.db.fetch_user(username)
    if user_inf == None:
        conn.sock.send(REQUEST_FIN + b"User not found!\n")
        raise StopIteration
    conn.sock.send(b"\x00Enter your password or /cancel to cancel: ")
    yield

    password = conn.msg.decode('UTF-8')
    if password == '/cancel':
        conn.sock.send(REQUEST_FIN + b'Request canceled.')
        raise StopIteration

    # check password from db
    if sha256((password + config.PASSWORD_SALT).encode()).hexdigest() != user_inf[2]:
        conn.sock.send(REQUEST_FIN + b'Password error!')
        raise StopIteration
    conn.sock.send(LOGIN_SUCCEED + 
        bytes( 'Welcome %s, please enter a command.'%username, 'ASCII'))
    print("User %s logged in." % (username,))
    conn.login = True
    conn.username = username
    server.login_connections[conn.sock.fileno()] = conn
    raise StopIteration

def ls_handler(conn, server):
    list_str = ""
    for conn in server.login_connections.values():
        list_str += "%s " % conn.username
    conn.sock.send(REQUEST_FIN + list_str.encode())
    raise StopIteration

REQUEST_HANDLERS = {
    REGISTER_REQUEST : register_handler,
    LOGIN_REQUEST : login_handler,
    LIST_REQUEST : ls_handler,
    DISCON_REQUEST : None,
    LOGOUT_REQUEST : None,
}

def handle_request(conn, server):
    msg = conn.sock.recv(4096)
    print("handling request from : " + str(conn.sock))
    print("receive raw msg : " + str(msg))
    # remote socket closed
    if msg == b'':
        raise socket.error

    if conn.task == None:
        print("Creating new task")
        request_type = bytes([msg[0]])
        msg = msg[1:]
        try:
            conn.task = REQUEST_HANDLERS[request_type](conn, server)
        except StopIteration:
            conn.task = None
            return
        except KeyError:
            conn.sock.send(REQUEST_FIN + b'Unestablished function.')
    print("Resuming Task")
    try:
        conn.msg = msg
        if conn.task != None:
            next(conn.task)
    except StopIteration:
        conn.task = None

if __name__ == '__main__':
    # setup the server
    server = Server(config.PORT)
    server.start()
