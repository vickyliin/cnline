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

def register_handler(conn, db):
    while True:
        conn.sock.send(b'''-----Registration-----\nPlease enter you username, or /cancel to cancel :''')
        yield
        username = conn.msg.decode('UTF-8')
        if username == '/cancel/':
            conn.task = None
            return
        r = db.fetch_user(username)
        if r != None:
            conn.sock.send(b"Sorry, this username is already used, please try with another.\n")
        else:
            break
    while True:
        conn.sock.send(b"Please enter you password:")
        yield
        password = conn.msg.decode('UTF-8')
        
        conn.sock.send(b"Please enter you password again:")
        yield
        password_2 = conn.msg.decode('UTF-8')

        if password == password_2:
            break
        else:
            conn.sock.send(b"Two password doesn't match!!\n")

    print("%s, %s" % (username, password))
    db.register(username, password)
    conn.sock.send(b"Success")
    conn.task = None
    
def login_handler(conn, db):
    username = conn.msg.decode('UTF-8')
    # check if username exists
    conn.sock.send(b'''Enter your password or /cancel to cancel: ''')
    yield
    password = conn.msg.decode('UTF-8')
    if password == '/cancel'
        conn.task = None
        return
    # check password from db
    conn.sock.send(b"Logged in!")
    print("User %s logged in." % (username,))
    conn.login = True
    conn.username = username
    conn.task = None

REQUEST_HANDLERS = {
    0x01 : register_handler,
    0x02 : login_handler
}

def handle_request(conn, db):
    msg = conn.sock.recv(4096)
    print("handling request from : " + str(conn.sock))
    print("receive raw msg : " + str(msg))
    # remote socket closed
    if msg == b'':
        raise socket.error

    if conn.task == None:
        print("Creating new task")
        request_type = msg[0]
        msg = msg[1:]
        conn.task = REQUEST_HANDLERS[request_type](conn, db)
    print("Resuming Task")
    try:
        conn.msg = msg
        next(conn.task)
    except StopIteration:
        conn.task = None

if __name__ == '__main__':
    # setup the server
    with socket.socket() as sock, select.epoll() as epoll:
        # Initialize sqlite db
        db = DBConnection()
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
                            handle_request(conn, db)
                        # remote socket closed
                        except socket.error as e:
                            print("connetion closed : " + str(conn.sock))
                            del connections[conn.sock.fileno()]
                            conn.sock.close()
        except KeyboardInterrupt:
            sock.close()
            exit()
