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
    def __init__(self):
        self.uid = None
        self.username = None
        self.loggedin = False
        self.last_login = ""
        self.sock = None

def DB_register(username, password):
    conn = sqlite.connect(config.USERS_DB_PATH)
    try:
        with conn:
            conn.execute('''INSERT INTO users(username, password, reg_time)
                            VALUES(?, ?, ?)''', (
                                username,
                                sha256((password + config.HASH_SALT).encode()).hexdigest(),
                                datetime.utcnow().isoformat(' ')
                            ))
    except sqlite3.Error as e:
        print("Database update failed : ", e.args[0])
        pass

def handle_request(sock):
    msg = sock.recv(4096).decode("UTF-8")
    print("receive : " + msg)
    pass

if __name__ == '__main__':

    # setup the server
    with socket.socket() as sock, select.epoll() as epoll:
        # bind the socket and register to epoll object
        sock.bind(("0.0.0.0", config.PORT))
        sock.listen(5)
        print("socket created : " + str(sock))
        epoll.register(sock.fileno(), select.EPOLLIN)

        connections = {}
        while True:
            for fd, event in epoll.poll():
                # accept new connections, register to epoll and add to connections dict
                if fd == sock.fileno():
                    conn, _ = sock.accept()
                    epoll.register(conn.fileno(), select.EPOLLIN)
                    connections[conn.fileno()] = conn
                # handle other requests
                elif event & select.EPOLLIN:
                    conn = connections[fd]
                    try:
                        handle_request(conn)
                    except socket.error as e:
                        print(e.args[0])
                        pass
