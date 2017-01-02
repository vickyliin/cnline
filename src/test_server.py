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
    print('%s %s' % (current_thread().name, msg), 
        flush=True, *arg, **kwarg)
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
            i,j = 0,0
            leave = False
            while(True):
                if leave:
                    connsock.send(REQUEST_FIN)
                    continue
                    
                msg = connsock.recv(4096)
                if msg == b'':
                    print('No msg, client may leave')
                    connsock.close()
                    break
                code, msg = msg[:1], msg[1:]
                print( '%s\t%s' % ( code_dict[code] , msg.decode() ) )
                if code == MSG_REQUEST:
                    # echo
                    msg = msg.decode().split('\n')[1].encode()
                    connsock.send( REQUEST_FIN + msg)
                elif code == TRANSFER_REQUEST:
                    # simulate the recver, toggle accept/deny
                    i += 1
                    if i%2 == 0:
                        connsock.send(TRANSFER_ACCEPT + b'ip:port')
                    else:
                        connsock.send(TRANSFER_DENY + b'Transfer denied by guest.')
                elif code == POLL_REQUEST:
                    # polling, simulate:
                    print(str(j))
                    j += 1

                    # peer leave chatroom
                    if j == 30:
                        connsock.send(LEAVE_REQUEST+b'guest\n')

                    elif j > 30:
                        connsock.send(REQUEST_FIN)

                    elif j == 1:
                        connsock.send(TALK_REQUEST+b'guest\n')


                    # file transfer request from remote
                    elif j%10 == 0:
                        connsock.send(TRANSFER_REQUEST+b'guest\n' + b'filename')
                    # msg from remote
                    elif j%5 == 3:
                        connsock.send(MSG_REQUEST+b'guest\nmsg')


                    # no new msg
                    else:
                        connsock.send(REQUEST_FIN)
                elif code == LEAVE_REQUEST:
                    leave = True
                    connsock.send(REQUEST_FIN)
                else:
                    connsock.send(REQUEST_FIN)
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
        print('Binding...')
        sock.bind(('0.0.0.0', port))
        print('PORT: %d'%port)
        sock.listen(5)
        while True:
            t = Thread(target=handler(sock))
            t.start()
            t.join()
