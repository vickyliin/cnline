#!/usr/bin/env python
# This is a test server, echo each message recieved from a client.
import socket
import config
from codes import *
from time import sleep
from threading import Thread, current_thread

import codes
code_dict = { v:k for k,v in codes.__dict__.items() \
                if not k.startswith('__') }
code_dict[b'\x00'] = 'DEFAULT'
def thprint(msg, *arg, **kwarg):
    print('%s %s' % (current_thread().name, msg), *arg, **kwarg)
def handler(sock, print=thprint):
    def handle():
        peer = None
        connsock = None
        try:
            connsock, _ = sock.accept()
            t = Thread(target=handler(sock))
            t.start()
            peer = connsock.getpeername()[0]
            print('IP %s connect' % peer)
            while(True):
                msg = connsock.recv(4096)
                if msg == b'':
                    print('No msg, client may leave')
                    connsock.close()
                    break
                code, msg = msg[:1], msg[1:]
                print( '%s\t%s' % ( code_dict[code] , msg.decode() ) )
                if code == MSG_REQUEST:
                    connsock.send( REQUEST_FIN + b'guest: ' + msg)
                elif code+msg == b'\x00A':
                    # polling, simulate file transfer request from remote
                    connsock.send(TRANSFER_REQUEST + b'filename')
                else:
                    connsock.send( MSG_REQUEST + b'msg ' + msg )
        except ConnectionResetError:
            print('IP %s leave' % peer)
        except OSError:
            print('IP %s leave' % peer)
        except KeyboardInterrupt:
            sock.close()
        finally:
            if connsock:
                connsock.close()
        return
    return handle
if __name__ == '__main__':
    # setup the server
    with socket.socket() as sock:
        connsock = None
        port = 16666
        sock.bind(('0.0.0.0', port))
        print('PORT: %d'%port)
        sock.listen(5)
        while True:
            t = Thread(target=handler(sock))
            t.start()
            t.join()
