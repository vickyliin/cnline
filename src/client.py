#!/usr/bin/env python3
import socket
import config


def login(sock):
    return 0

def register(sock):
    return 0

if __name__ == "__main__":
    print("Welcome to CNLINE! Connecting to server...")
    with socket.socket() as sock:
        sock.connect((config.SEVER_IP, PORT))
        print("Connection established, please enter a command (login/register/exit)\n> ", end="")
        while(True):
            usrcmd = input()
            if usrcmd.startswith("login"):
                login(sock)
            elif usrcmd.startswith("register"):
                register(sock)
            elif usrcmd.startswith("exit"):
                print("Goodbye~")
                break
            else:
                print("Unrecognizable command! Please enter one of the following commands (login/register/exit)\n> ", end="")
    return 0
