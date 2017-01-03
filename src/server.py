#!/usr/bin/env python3

import sqlite3
import os
import socket
import selectors
from hashlib import sha256
from datetime import datetime
from codes import *
import config

def sha256_str(txt, salt):
    return sha256((txt + salt).encode()).hexdigest()

def utcnow_iso():
    return datetime.utcnow().isoformat(' ')
    
class Server:
    def __init__(self):
        self.login_connections = {}
        self.connections = {}

    def start(self, port):
        self.db = DBConnection()
        with socket.socket() as svr_sock, selectors.DefaultSelector() as sel:
            try:
                # bind the socket and register to selector object
                svr_sock.bind(("0.0.0.0", port))
                svr_sock.listen(5)
                print("socket created : " + str(svr_sock))
                sel.register(svr_sock, selectors.EVENT_READ)

                while True:
                    for key, event in sel.select():
                        # accept new connections, register to selector
                        if key.fd == svr_sock.fileno():
                            connsock, _ = svr_sock.accept()
                            print("accept new connetion : " + str(connsock))
                            sel.register(connsock, selectors.EVENT_READ)
                            # Create connection object, store into dict
                            conn = Connection(connsock)
                            self.connections[connsock.fileno()] = conn
                        # handle other request
                        elif event & selectors.EVENT_READ:
                            conn = self.connections[key.fd]
                            try:
                                handle_request(conn, self)
                            # remote socket closed
                            except socket.error as e:
                                print("connetion closed : " + str(conn.sock))
                                if conn.username in self.login_connections:
                                    del self.login_connections[conn.username]
                                del self.connections[conn.sock.fileno()]
                                conn.sock.close()
            except KeyboardInterrupt:
                svr_sock.close()
                self.db.close()
                exit()

class Connection:
    def __init__(self, sock):
        self.uid = None
        self.username = None
        self.last_login = ""
        self.sock = sock
        self.task = None
        self.buf = b""

    def recv(self):
        self.buf = self.sock.recv(4096)

    def send(self, code, msg):
        self.sock.send(code + msg.encode())

    def set_info(self, user_inf):
        self.uid = user_inf[0]
        self.username = user_inf[1]
        self.last_login = user_inf[-1]

class DBConnection:
    def __init__(self):
        self.conn = sqlite3.connect(config.USERS_DB_PATH)
    def register(self, username, password):
        with self.conn:
            self.conn.execute('''INSERT INTO users(username, password, reg_time)
                                 VALUES(?, ?, ?)''', (
                                     username,
                                     sha256_str(password, config.PASSWORD_SALT),
                                     utcnow_iso()
                             ))

    def fetch_user(self, username):
        with self.conn:
            self.cur = self.conn.cursor()
            self.cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self.cur.fetchone()

    def close(self):
        self.conn.close()

    def save_message(self, message, users):
        with self.conn:
            self.conn.execute('''INSERT INTO messages(src, dest, time, msg, read)
                                 VALUES(?, ?, ?, ?, ?)''', (
                                     *users, utcnow_iso(), message, 0
                             ))
    
    def query_messages(self, src, dest, num):
        with self.conn:
            self.cur = self.conn.cursor()
            self.cur.execute('''SELECT * FROM (
                                    SELECT * FROM messages
                                     WHERE (src = ? AND dest = ?) OR (src = ? AND dest = ?)
                                     ORDER BY id DESC
                                     LIMIT 0, ?
                                ) ORDER BY id ASC'''
                             (src, dest, dest, src, num))
            result = self.cur.fetchall()
        return result

    def update_user(self, username):
        with self.conn:
            self.conn.execute('''UPDATE users SET last_login = ? WHERE username = ?''', (
                                    utcnow_iso(), username
                             ))

def register_handler(conn, server):
    while True:
        # ask for username
        conn.send(NULL, "-----Registration-----\nPlease enter you username, or /cancel to cancel :")
        yield

        username = conn.buf
        if username == "/cancel":
            conn.send(REQUEST_FIN, 'Request canceled.')
            raise StopIteration
        # check if username already in use.
        if server.db.fetch_user(username) == None:
            break
        conn.send(NULL, "Sorry, this username is already used, please try with another.\n")

    while True:
        # ask for password
        conn.send(NULL, "Please enter you password:")
        yield

        password = conn.buf
        # confirm password
        conn.send(NULL, "Please enter you password again:")
        yield

        password_2 = conn.buf
        if password == password_2:
            break
        conn.send(NULL, "Two password doesn't match!!\n")

    print("%s, %s" % (username, password))
    server.db.register(username, password)
    conn.send(REQUEST_FIN, " Registration Success!")
    raise StopIteration
    
def login_handler(conn, server):
    username = conn.buf
    # check if username exists
    user_inf = server.db.fetch_user(username)
    if user_inf == None:
        conn.send(REQUEST_FIN, "User not found!\n")
        raise StopIteration
    conn.send(NULL, "Enter your password or /cancel to cancel: ")
    yield

    password = conn.buf
    if password == '/cancel':
        conn.send(REQUEST_FIN, 'Request canceled.')
        raise StopIteration

    # check password from db
    if sha256((password + config.PASSWORD_SALT).encode()).hexdigest() != user_inf[2]:
        conn.send(REQUEST_FIN, 'Password error!')
        raise StopIteration
    conn.send(LOGIN_SUCCEED, 'Welcome %s, please enter a command.' % username)
    print("User %s logged in." % (username,))
    server.db.update_user(username)
    server.login_connections[username] = conn
    conn.set_info(user_inf)
    raise StopIteration

def ls_handler(conn, server):
    if False:
        yield
    list_str = " ".join(server.login_connections)
    conn.send(REQUEST_FIN, list_str)
    raise StopIteration

def logout_handler(conn, server):
    if False:
        yield
    del server.login_connections[conn.username]
    conn.send(LOGOUT_SUCCEED, "")
    raise StopIteration

def message_handler(conn, server):
    if False:
        yield
    src = conn.username
    dest, msg = conn.buf.split('\n')
    conn.send(REQUEST_FIN, msg)

    sent = 0
    if dest in server.login_connections:
        server.login_connections[dest].send(MSG_REQUEST, src + '\n' + msg)
        sent = 1
    raise StopIteration

REQUEST_HANDLERS = {
    REGISTER_REQUEST : register_handler,
    LOGIN_REQUEST : login_handler,
    LIST_REQUEST : ls_handler,
    DISCON_REQUEST : None,
    LOGOUT_REQUEST : logout_handler,
    MSG_REQUEST : message_handler,
}

def handle_request(conn, server):
    conn.recv()
    print("handling request from : " + str(conn.sock))
    print("receive raw msg : " + str(conn.buf))
    # remote socket closed
    if conn.buf == b'':
        raise socket.error

    if conn.task == None:
        print("Creating new task")
        request_type, conn.buf = conn.buf[:1], conn.buf[1:]
        try:
            conn.task = REQUEST_HANDLERS[request_type](conn, server)
        except KeyError:
            conn.send(REQUEST_FIN, 'Unestablished function.')
    conn.buf = conn.buf.decode("UTF-8")
    print("Resuming Task with buf = " + str(conn.buf))
    try:
        if conn.task != None:
            next(conn.task)
    except StopIteration:
        conn.task = None

if __name__ == '__main__':
    # starts the server
    server = Server()
    server.start(config.PORT)
