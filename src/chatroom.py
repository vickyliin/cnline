#!/usr/bin/env python3
from util import *

from transfer import *
from history import *

class ChatroomManager():
    # the manager will 
    # 1) create a thread to poll requess from server
    # 2) record file receiving status
    # 3) build a chatroom as recving a talk request
    # 4) record the file recving ports
    # 5) record the existing chatrooms

    def __init__(self, sock, username=None):
        self.username = username
        self.chatrooms = {}
        self.fileports = queue.Queue(MAX_TRANS_AMT)
        self.chatroom_lock = Lock()
        self.socket_lock = Lock()
        self.tkroot = tk.Tk()

        for i in range(MAX_TRANS_AMT):
            self.fileports.put(i + FILE_PORT)

        self.server = sock.getpeername()
        self.sock = sock

    def start(self):
        self.alive = True

        self.rsock = socket.socket()
        self.rsock.connect(self.server)
        self.tkroot.protocol('WM_DELETE_WINDOW', self.close)
        self.tkroot.after(0, self.poll)

        self.tkroot.mainloop()

    def poll(self):
        # create a new socket to poll talk request from another user
        # a new socket is created to avoid sync receiving problem
        sock = self.rsock
        try:
            sock.send(POLL_REQUEST + self.username.encode())
            server_msg = sock.recv(MAX_RECV_LEN)
        except OSError:
            return
        code, msg = server_msg[:1], server_msg[1:]

        if code == REQUEST_FIN:
            self.tkroot.after(1000, self.poll)
            return

        guest, msg = msg.decode().split('\n')

        if code != TALK_REQUEST:
            try:
                chatroom = self.chatrooms[guest]
            except KeyError:
                self.tkroot.after(1000, self.poll)
                return
            

        if code == TALK_REQUEST:
            # build a new chatroom and start
            self.build(guest)
            chatroom = self.chatrooms[guest]
            chatroom.root.after(1000, self.poll)
            chatroom.root.mainloop()

        elif chatroom.alive:
            if code == MSG_REQUEST:
                # print on the corresponding chatroom
                chatroom.print('[%s]: %s' % (guest,msg))

            elif code == TRANSFER_REQUEST:
                # create a thread to recv file
                filename = msg
                thpack(recv_file, chatroom, filename)()

            elif code == LEAVE_REQUEST:
                # peer leave the chatroom
                chatroom.print('%s leave the chatroom.' % \
                    chatroom.guest)
                chatroom.kill()

        if self.alive:
            self.tkroot.after(1000, self.poll)

    def build(self, guest):
        self.chatroom_lock.acquire()
        new_chatroom = Chatroom(
            fileports = self.fileports,
            root = self.tkroot,
            lock = self.socket_lock,
            host = self.username,
            guest = guest
        )
        
        self.chatrooms[guest] = new_chatroom

        new_chatroom.start(self.sock)
        self.chatroom_lock.release()

    def close(self):
        self.tkroot.destroy()
        self.chatroom_lock.acquire()
        for (guest, chatroom) in self.chatrooms.items():
            if chatroom.alive:
                chatroom.alive = False
                chatroom.send(LEAVE_REQUEST)
                chatroom.recv()
        self.chatroom_lock.release()
        self.alive = False
        self.rsock.close()

class Chatroom():
    def __init__(self, fileports, root, host, guest, lock):
        # init tk window
        self.host = host
        self.guest = guest

        self.root = tk.Toplevel(root)
        self.root.title(guest)
        self.alive = False
        self.fileports = fileports
        self.lock = lock

        # add elements in the window
        self.chatbox = tk.Text(self.root)
        self.msgbar = tk.Entry(self.root)
        self.filebtn = tk.Button(self.root, text='File')
        self.histbtn = tk.Button(self.root, text='History')

        self.elements = [ 
            # (tk object, bind event, event reaction, offline access)
            (self.chatbox, None, None, True),
            (self.msgbar, '<Return>', send_msg, False),
            (self.filebtn, '<Button-1>', req_file, False),
            (self.histbtn, '<Button-1>', req_hist, True),
        ]

        # TODO arrange the elements


    def start(self, sock):
        # sock: initiative sending message
        self.sock = sock

        for (tkobj, event, funct, offline) in self.elements:
            # pack elements in the window to show them in mainloop
            tkobj.pack()
            # add event listenners
            if event:
                tkobj.bind(event, thpack(funct, self))

        # user close the window
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # open the window
        self.alive = True

    def print(self, msg, end='\n'):
        if type(msg) == bytes:
            msg = msg.decode()
        self.chatbox.insert('1.0', msg+end)

    def send(self, code, msg=b''):
        if type(msg) != bytes:
            msg = ('%s' % msg).encode()
        self.lock.acquire()
        self.sock.send(
            code +
            ( self.guest +'\n' ).encode() +
            msg
        )
    def recv(self):
        server_msg = self.sock.recv(MAX_RECV_LEN)
        self.lock.release()
        return server_msg

    def close(self): 
        # user close the window
        self.alive = False 
        self.send(LEAVE_REQUEST)
        self.recv()
        self.root.destroy()

    def kill(self):
        # the chatroom kill itself
        self.alive = False

        # close the functions not apply offline access 
        for (tkobj, event, funct, offline) in self.elements:
            if not offline:
                tkobj.bind(event, self.dead_note)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def dead_note(self, *arg):
        self.print('The chatroom is not alive.')

def send_msg(chatroom):
    # do when press enter in the msgbar:
    # send a msg to server and 
    # print the recving msg when code = REQUEST_FIN

    msg = chatroom.msgbar.get()
    username = chatroom.host
    chatroom.send(MSG_REQUEST, msg)
    try:
        server_msg = chatroom.recv()
    except socket.timeout:
        chatroom.print('Timeout, trying to send again.')
        server_msg = chatroom.recv()

    code, echo_msg = server_msg[:1], server_msg[1:].decode()
    if code == REQUEST_FIN:
        chatroom.print('[%s]: %s' % (username,echo_msg))
        chatroom.msgbar.delete(0, tk.END)
    else:
        chatroom.print('Error, please send your message again.')
    return

if __name__ == '__main__':
    # This section is for unit test.
    # TODO Remove this as client gui part done
    MAX_TRANS_AMT = 11
    server = ('localhost', 16666)
    FILE_PORT = 16888

    sock = socket.socket()
    try:
        sock.connect(server)
        manager = ChatroomManager(
            username = 'host',
            sock = sock
        )
        manager.start()
    except OSError as e:
        print('Connection failed.')
        print(e)
        sock.close()
        exit()
    finally:
        sock.close()
