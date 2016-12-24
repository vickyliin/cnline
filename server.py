#!/usr/bin/env python3

import sqlite3
import os
import sys
import socket
import select
from hashlib import sha256
from datetime import datetime
import config

class Connection:
    def __init__(self, sock):
        self.uid = None
        self.username = None
        self.login = False
        self.last_login = ""
        self.last_logout = ""
        self.sock = sock
        self.task = None

def register_handler(conn):
    conn.sock.send(b'''-----Registration-----
                       Please enter you username:''')
    yield
    username = conn.msg
    # check username
    conn.sock.send(b'''Please enter you password:''')
    yield
    password = conn.msg
    print("%s, %s" % (username, password))
    conn.task = None
    
def login_handler(conn):
    username = conn.msg
    conn.sock.send(b'''Enter your password : ''')
    yield
    password = conn.msg
    #check password from db
    conn.sock.send(b"Logged in!")
    print("User %s logged in." % (username,))
    conn.login = True
    conn.username = username
    self.task = None

REQUEST_HANDLERS = {
    0x01 : register_handler,
    0x02 : login_handler
}

def DB_register(username, password):
    conn = sqlite.connect(config.USERS_DB_PATH)
    try:
        with conn:
            conn.execute('''INSERT INTO users(username, password, reg_time)
                            VALUES(?, ?, ?)''', (
                                username,
                                sha256((password + config.PASSWORD_SALT).encode()).hexdigest(),
                                datetime.utcnow().isoformat(' ')
                            ))
    except sqlite3.Error as e:
        print("Database update failed : ", e.args[0])
        pass

def handle_request(conn):
    msg = conn.sock.recv(4096)
    print("handling request from : " + str(conn.sock))
    print("receive raw msg : " + str(msg))
    # remote socket closed
    if msg == b'':
        raise socket.error

    if conn.task == None:
        print("Creating new task")
        request_type = msg[0]
        msg = msg[1:].decode("UTF-8")
        conn.task = REQUEST_HANDLERS[request_type](conn)
    print("Resuming Task")
    try:
        conn.msg = msg
        next(conn.task)
    except StopIteration:
        conn.task = None

if __name__ == '__main__':
    # setup the server
    with socket.socket() as sock, select.epoll() as epoll:
        try:
            # bind the socket and register to epoll object
            sock.bind(("0.0.0.0", config.PORT))
            sock.listen(5)
            print("socket created : " + str(sock))
            epoll.register(sock.fileno(), select.EPOLLIN)

            connections = {}
            while True:
                for fd, event in epoll.poll():
                    # accept new connections, register to epoll
                    if fd == sock.fileno():
                        connsock, _ = sock.accept()
                        print("accept new connetion : " + str(connsock))
                        epoll.register(connsock.fileno(), select.EPOLLIN)
                        # Create connection object, store into dict
                        conn = Connection(connsock)
                        connections[conn.sock.fileno()] = conn
                    # handle other requests
                    elif event & select.EPOLLIN:
                        conn = connections[fd]
                        try:
                            handle_request(conn)
                        # remote socket closed
                        except socket.error as e:
                            print("connetion closed : " + str(conn.sock))
                            del connections[conn.sock.fileno()]
                            conn.sock.close()
        except KeyboardInterrupt:
            sock.close()
