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
                                sel.unregister(conn.sock)
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
        self.transfer_list = []

    def recv(self):
        self.buf = self.sock.recv(4096)

    def send(self, code, msg):
        self.sock.send(code + msg.encode())

    def msgsend(self, msg):
        self.rsock.send(MSG_REQUEST + msg.encode() + REQUEST_FIN)

    def histsend(self, guest, msg):
        self.rsock.send(HISTORY_REQUEST + (guest + '\n' + msg).encode() + REQUEST_FIN)

    def filesend(self, guest, filename):
        self.rsock.send(TRANSFER_REQUEST + (guest + '\n' + filename).encode() + REQUEST_FIN)

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

    def save_message(self, users, message, sent):
        with self.conn:
            self.conn.execute('''INSERT INTO messages(src, dest, time, msg, read)
                                 VALUES(?, ?, ?, ?, ?)''', (
                                     *users, utcnow_iso(), message, sent
                             ))
    
    def query_messages(self, src, dest, num):
        with self.conn:
            self.cur = self.conn.cursor()
            self.cur.execute('''SELECT * FROM (
                                    SELECT * FROM messages
                                     WHERE (src = ? AND dest = ?) OR (src = ? AND dest = ?)
                                     ORDER BY id DESC
                                     LIMIT 0, ?
                                ) ORDER BY id ASC''',
                             (src, dest, dest, src, num))
            result = self.cur.fetchall()
        return result

    def update_user(self, username):
        with self.conn:
            self.conn.execute('''UPDATE users SET last_login = ? WHERE username = ?''', (
                                    utcnow_iso(), username
                             ))

    def query_unread(self, username):
        with self.conn:
            self.cur = self.conn.cursor()
            self.cur.execute('''SELECT * FROM messages WHERE dest = ? AND read = 0''', (username, ))
            result = self.cur.fetchall()
        return result

    def update_unread(self, username):
        with self.conn:
            self.conn.execute('''UPDATE messages SET read = 1 WHERE dest = ?''', (username,))

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
        server.login_connections[dest].msgsend(src + '\n' + msg)
        sent = 1

    server.db.save_message((src, dest), msg, sent)
    raise StopIteration

def rsock_init(conn, server):
    if False:
        yield
    username = conn.buf
    server.login_connections[username].rsock = conn.sock

    # check unread messages
    unread = server.db.query_unread(username)
    for row in unread:
        server.login_connections[username].msgsend(row[1] + '\n' + row[4])
    server.db.update_unread(username)
    raise StopIteration

def history_handler(conn, server):
    if False:
        yield
    conn.send(REQUEST_FIN, '')
    dst, count = conn.buf.split('\n')
    result = server.db.query_messages(conn.username, dst, int(count))
    for row in result:
        conn.histsend(dst, row[4])
    conn.rsock.send(HISTORY_END)
    raise StopIteration

def transfer_handler(conn, server):
    if False:
        yield
    dst, filename = conn.buf.split('\n')
    if not dst in server.login_connections:
        conn.send(TRANSFER_DENY, "Peer isn't online.")
        raise StopIteration

    print("asking %s to recv file" % dst)
    server.login_connections[dst].filesend(conn.username, filename)
    raise StopIteration

def transfer_accept(conn, server):
    if False:
        yield
    dst, port = conn.buf.split('\n')
    print("accept, sent response to dst %s" % dst)
    if dst in server.login_connections:
        print("sent to ", conn.sock.getpeername()[0] + ":" + port)
        server.login_connections[dst].send(TRANSFER_ACCEPT, conn.sock.getpeername()[0] + ":" + port)
    conn.send(REQUEST_FIN, "")
    raise StopIteration


def transfer_deny(conn, server):
    if False:
        yield
    dst = conn.buf.strip('\n')
    print("deny, sent response to dst %s" % dst)
    if dst in server.login_connections:
        server.login_connections[dst].send(TRANSFER_DENY, "Request denied by peer.")
    conn.send(REQUEST_FIN, "")
    raise StopIteration

REQUEST_HANDLERS = {
    REGISTER_REQUEST : register_handler,
    LOGIN_REQUEST : login_handler,
    LIST_REQUEST : ls_handler,
    DISCON_REQUEST : None,
    LOGOUT_REQUEST : logout_handler,
    MSG_REQUEST : message_handler,
    RSOCK_INIT : rsock_init,
    HISTORY_REQUEST : history_handler,
    TRANSFER_REQUEST : transfer_handler,
    TRANSFER_ACCEPT : transfer_accept,
    TRANSFER_DENY : transfer_deny,
}

def handle_request(conn, server):
    conn.recv()
    print("handling request from : " + str(conn.sock))
    print("receive raw msg : " + str(conn.buf))
    # remote socket closed
    if conn.buf == b'':
        raise socket.error

    if conn.task == None:
        request_type, conn.buf = conn.buf[:1], conn.buf[1:]
        try:
            conn.task = REQUEST_HANDLERS[request_type](conn, server)
        except KeyError:
            conn.send(REQUEST_FIN, 'Unestablished function.')
    conn.buf = conn.buf.decode("UTF-8")
    try:
        if conn.task != None:
            next(conn.task)
    except StopIteration:
        conn.task = None

if __name__ == '__main__':
    # starts the server
    server = Server()
    server.start(config.PORT)
