#!/usr/bin/env python

import socket
import config
from codes import *

if __name__ == '__main__':
    # setup the server
    sock = socket.socket()
    connsock = None
    try:
        sock.bind(('0.0.0.0', config.PORT))
        print('PORT: %d'%config.PORT)
        sock.listen(5)
        connsock, _ = sock.accept()
        while(True):
            msg = connsock.recv(4096)
			code, msg = msg[:1], msg[1:]
            print( '%d %s'%(code,msg.decode()) )
            if code == LOGIN_REQUEST:
                connsock.send( LOGIN_SUCCEED + msg)
            elif code == TALK_REQUEST:
                connsock.send( TALK_SUCCEED + msg)
            elif code == LOGOUT_REQUEST:
                connsock.send( LOGOUT_SUCCEED + msg)
            elif code == MSG_REQUEST:
                connsock.send( MSG_REQUEST + msg)
            else:
                connsock.send(
                    bytes([SERVER_CODE['req_end']])+ msg)
    except KeyboardInterrupt:
        connsock.close()
    except ConnectionResetError:
        pass
    finally:
        sock.close()
