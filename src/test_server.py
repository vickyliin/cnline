#!/usr/bin/env python

import socket
from config import *

if __name__ == '__main__':
    # setup the server
    sock = socket.socket()
    connsock = None
    try:
        sock.bind(('0.0.0.0', PORT))
        print('PORT: %d'%PORT)
        sock.listen(5)
        while(True):
            connsock, _ = sock.accept()
            msg = connsock.recv(4096)
            code = msg[0]
            msg = msg[1:]
            print( '%d\t%s'%(code,msg.decode()) )
            if code == REQUEST_CODE['login']:
                connsock.send(
                    bytes([SERVER_CODE['logout_succeed']])+ msg)
            elif code == REQUEST_CODE['talk']:
                connsock.send(
                    bytes([SERVER_CODE['talk_req_succeed']])+ msg)
            elif code == REQUEST_CODE['logout']:
                connsock.send(
                    bytes([SERVER_CODE['logout_req_succeed']])+ msg)
            else:
                connsock.send(
                    bytes([SERVER_CODE['req_end']])+ msg)
            connsock.close()
    except KeyboardInterrupt:
        connsock.close()
    finally:
        sock.close()
