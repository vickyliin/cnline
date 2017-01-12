#!/usr/bin/env python3
from util import *

from transfer import *
from history import *

class LoginManager():
    # the manager will 
    # 1) poll for server msg
    # 2) build a chatroom as recving a msg/file transfer request
    # 3) record the file recving ports
    # 4) record the existing chatrooms
    # 5) ls, talk, logout

    def __init__(self, sock, username=None):
        self.username = username
        self.chatrooms = {}
        self.fileports = queue.Queue(MAX_TRANS_AMT)
        self.chatroom_lock = Lock()
        self.socket_lock = Lock()
        self.tkroot = tk.Tk()
        self.login = True

        self.tkroot.title('CNLine')

        self.elements = []
        button_text = ['Online Users', 'New Chatroom', 'Logout']
        button_commands = [self.ls, self.new, self.logout]

        self.msgbox = tk.Text(self.tkroot)
        self.elements.append(self.msgbox)
        for text,command in zip(button_text, button_commands):
            self.elements.append(tk.Button(
                self.tkroot, 
                text=text,
                command=command
            ))

        for i in range(MAX_TRANS_AMT):
            self.fileports.put(i + config.FILE_PORT)

        self.server = sock.getpeername()
        self.sock = sock

        self.selector = DefaultSelector()

    def send(self, code, msg=b''):
        if type(msg) != bytes:
            msg = ('%s' % msg).encode()
        self.socket_lock.acquire()
        self.sock.send( code + msg )
    def recv(self):
        server_msg = self.sock.recv(MAX_RECV_LEN)
        self.socket_lock.release()
        return server_msg
    def print(self, msg, end='\n'):
        if type(msg) == bytes:
            msg = msg.decode()
        self.msgbox.insert('1.0', msg+end)

    def ls(self):
        self.send(LIST_REQUEST)
        server_msg = self.recv()
        code, msg = server_msg[:1], server_msg[1:]
        self.print('--------------------------------------')
        self.print(msg)
        self.print('\n--------------------------------------')
    def logout(self):
        self.send(LOGOUT_REQUEST)
        self.recv()
        self.close()
        self.login = False
    def new(self):
        guest = 'username'
        guest = tksd.askstring('New Chatroom', 'To:')
        if guest:
            self.build(guest)
            chatroom = self.chatrooms[guest]
            chatroom.root.after(1000, self.poll)
            chatroom.root.mainloop()

    def start(self):
        self.alive = True
        for element in self.elements:
            element.pack()

        self.rsock = socket.socket()
        self.rsock.connect(self.server)
        self.rsock.send(RSOCK_INIT + self.username.encode())
        self.selector.register(self.rsock, EVENT_READ)

        self.tkroot.protocol('WM_DELETE_WINDOW', self.close)
        self.tkroot.after(0, self.poll)
        self.tkroot.attributes("-topmost", True)

        self.tkroot.mainloop()

    def poll(self):
        # create a new socket to poll talk request from another user
        # a new socket is created to avoid sync receiving problem
        events = self.selector.select(0)
        for key, mask in events:
            sock = key.fileobj
            try:
                server_msg = sock.recv(MAX_RECV_LEN)
            except OSError:
                return
            for msg in server_msg.split(REQUEST_FIN)[:-1]:
                
                print(msg)
                code, msg = msg[:1], msg[1:]

#                if code == REQUEST_FIN:
#                    self.tkroot.after(1, self.poll)
#                    return
                guest, msg = msg.decode().split('\n')

                try:
                    chatroom = self.chatrooms[guest]
                    new_chatroom = False
                except KeyError:
                    # build a new chatroom and start
                    new_chatroom = True
                    self.build(guest)
                    chatroom = self.chatrooms[guest]
#                    chatroom.root.after(1, self.poll)

                if not chatroom.alive:
                    new_chatroom = True
                    self.build(guest)
                    chatroom = self.chatrooms[guest]
#                    chatroom.root.after(1, self.poll)

                if code == MSG_REQUEST:
                    # print on the corresponding chatroom
                    chatroom.print('[%s]: %s' % (guest,msg))

                elif code == TRANSFER_REQUEST:
                    # create a thread to recv file
                    filename = msg
                    thpack(recv_file, chatroom, filename)()


            if new_chatroom:
                print("Creating new chatroom")
                chatroom.root.mainloop()
#                if self.alive:
#                    self.tkroot.after(1, self.poll)
        self.tkroot.after(1, self.poll)

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
        self.chatroom_lock.release()
        self.alive = False
        self.rsock.close()

class Chatroom:
    def __init__(self, fileports, root, host, guest, lock):
        # init tk window
        self.host = host
        self.guest = guest

        self.root = tk.Toplevel(root)
        self.root.title('To: '+guest+' / '+host)
        self.alive = False
        self.fileports = fileports
        self.lock = lock

        # add elements in the window
        self.chatbox = tk.Text(self.root)
        self.msgbar = tk.Entry(self.root)
        self.filebtn = tk.Button(self.root, text='File')
        self.histbtn = tk.Button(self.root, text='History')

        self.elements = [ 
            (self.chatbox, None, None),
            (self.msgbar, '<Return>', send_msg),
            (self.filebtn, '<Button-1>', req_file),
            (self.histbtn, '<Button-1>', req_hist),
        ]

        # TODO arrange the elements


    def start(self, sock):
        # sock: initiative sending message
        self.sock = sock

        for (tkobj, event, funct) in self.elements:
            # pack elements in the window to show them in mainloop
            tkobj.pack()
            # add event listenners
            if event:
                tkobj.bind(event, thpack(funct, self))

        # user close the window
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # open the window
        self.alive = True
        self.root.attributes("-topmost", True)

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
        self.lock.acquire()
        self.alive = False 
        self.root.destroy()
        self.lock.release()

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
    server = ('localhost', 16666)
    FILE_PORT = 16888

    sock = socket.socket()
    try:
        sock.connect(server)
        manager = LoginManager(
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
