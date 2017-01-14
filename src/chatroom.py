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
        self.login = True
        self.history = False
        self.after = None

        self.tkroot = tk.Tk()
        self.tkroot.title('CNLine / %s' % username)
        win_config_set(self.tkroot)

        self.elements = []

        self.msgbox = tk.Text(self.tkroot)
        text_config_set(self.msgbox, h=6)

        #self.elements.append(self.msgbox)

        button_text = ['Online Users', 'New Chatroom', 'Logout']
        button_commands = [self.ls, self.new, self.logout]
        for text,command in zip(button_text, button_commands):
            button = tk.Button(
                self.tkroot, 
                text=text,
            )
            button_config_set(button, command)
            self.elements.append(button)

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

    def print(self, *args, **kwargs):
        text_print(self.msgbox, *args, **kwargs)
        
    def ls(self):
        self.send(LIST_REQUEST)
        server_msg = self.recv()
        code, msg = server_msg[:1], server_msg[1:]
        self.print('Online Users', tag=('start','history', 'title'))
        self.print(b'\n'.join(msg.split(b' ')), tag=('end','history'))
        self.print('')

    def logout(self):
        self.send(LOGOUT_REQUEST)
        self.recv()
        self.close()
        self.login = False
    def new(self):
        guest = tksd.askstring('New Chatroom', 'To:')
        if guest in self.chatrooms:
            self.print('The chatroom is already open.')
            chatroom = self.chatrooms[guest]
            chatroom.root.lower(belowThis=None)
        elif guest == self.username:
            self.print('Cannot send message to yourself.')
        elif guest:
            self.chatroom_lock.acquire()
            self.build(guest)
            self.remove(guest)

    def start(self):
        self.alive = True
        self.msgbox.pack(expand=True, fill='x')
        for button in self.elements:
            button.pack(
                side='left', 
                expand=True, 
                fill='x', 
                ipady=10,
            )

        self.rsock = socket.socket()
        self.rsock.connect(self.server)
        self.rsock.send(RSOCK_INIT + self.username.encode())
        self.selector.register(self.rsock, EVENT_READ)

        self.tkroot.protocol('WM_DELETE_WINDOW', self.close)
        self.tkroot.after(0, self.poll)
        self.print('Welcome, %s!' % self.username, tag=('title','start','end', 'history'))
        self.print('Press the buttons below, and enjoy your chatting!', tag='history')
        self.print('')
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
                code, msg = msg[:1], msg[1:]

                msg = msg.decode().split('\n')
                guest = msg[0]

                self.chatroom_lock.acquire()
                if guest in self.chatrooms:
                    new_chatroom = False
                    chatroom = self.chatrooms[guest]
                else:
                    # build a new chatroom and start
                    new_chatroom = True
                    self.build(guest)
                    chatroom = self.chatrooms[guest]

                if code == MSG_REQUEST:
                    msg = msg[1]
                    # print on the corresponding chatroom
                    chatroom.print(
                        '[%s]    %s' % (guest,msg),
                        tag='guest')

                elif code == HISTORY_REQUEST:
                    source, msg = msg[1], msg[2]
                    if not self.history:
                        chatroom.print( ' '*100, 
                            tag=('start', 'history'))
                        self.history = True
                    
                    if source == guest:
                        chatroom.print(
                            '[%s]    %s' % (source,msg),
                            tag=('guest', 'history')
                        )
                    else:
                        chatroom.print(
                            '%s    [%s]' % (msg, source),
                            tag=('host', 'history')
                        )

                elif code == HISTORY_END:
                    chatroom.print( ' '*100, 
                        tag=('end', 'history'))
                    self.history = False

                elif code == TRANSFER_REQUEST:
                    # create a thread to recv file
                    filename = msg[1]
                    thpack(recv_file, chatroom, filename)()

                self.chatroom_lock.release()
                if new_chatroom:
                    self.remove(guest)
                    return

        self.after = self.tkroot.after(1, self.poll)


    def build(self, guest):
        new_chatroom = Chatroom(
            fileports = self.fileports,
            root = self.tkroot,
            lock = self.socket_lock,
            host = self.username,
            guest = guest,
            room_lock = self.chatroom_lock,
        )
        
        self.chatrooms[guest] = new_chatroom

        self.print('New: %s' % guest)
        self.print(' / '.join(self.chatrooms.keys()), tag='end')

        new_chatroom.start(self.sock)

    def remove(self, guest):
        chatroom = self.chatrooms[guest]

        after = self.tkroot.after(1, self.poll)
        try:
            self.chatroom_lock.release()
        except RuntimeError:
            pass
        self.tkroot.wait_window(chatroom.root)

        self.chatroom_lock.acquire()
        try:
            del(self.chatrooms[guest])
            self.print('Close: %s' % guest)
            self.print(' / '.join(self.chatrooms.keys()), tag='end')
            self.tkroot.after_cancel(after)
        except KeyError:
            pass
        self.chatroom_lock.release()


    def close(self):
        self.chatroom_lock.acquire()
        for guest, chatroom in self.chatrooms.items():
            chatroom.root.destroy()
        self.chatrooms = {}
        self.alive = False
        self.rsock.close()
        self.tkroot.destroy()
        if self.after:
            self.tkroot.after_cancel(self.after)
        self.chatroom_lock.release()

class Chatroom:
    def __init__(self, fileports, 
        root, host, guest, 
        lock, room_lock):
        # init tk window
        self.host = host
        self.guest = guest

        self.root = tk.Toplevel(root)
        self.root.title('To: '+guest+' / '+host)
        self.alive = False
        self.fileports = fileports
        self.lock = lock
        self.after = None
        self.room_lock = room_lock

        # add elements in the window
        self.chatbox = tk.Text(self.root)

        self.msgbar = tk.Entry(self.root)
        self.filebtn = tk.Button(self.root, text='File')
        self.histbtn = tk.Button(self.root, text='History')

        win_config_set(self.root)
        text_config_set(self.chatbox)

        button_config_set(self.filebtn, thpack(req_file, self))
        button_config_set(self.histbtn, thpack(req_hist, self))

        self.msgbar.configure(
            borderwidth = 0,
            background='#eeeeee',
            font = ('Times', 14, 'normal'),
            relief='flat',
            selectborderwidth=0,
            textvariable = 1,
        )



        self.chatbox.configure(
            borderwidth = 0,
            state = 'disabled',
        )

        # TODO arrange the elements


    def start(self, sock):
        # sock: initiative sending message
        self.sock = sock

        self.msgbar.bind('<Return>', thpack(send_msg, self))

        self.chatbox.pack(expand=True, fill='x')
        pad = 6
        self.msgbar.pack(
            expand=True, 
            fill='x', 
            side='left',
            ipady=pad,
        )
        self.filebtn.pack(side='left', ipady=pad)
        self.histbtn.pack(side='left', ipady=pad)

        # user close the window
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # open the window
        self.alive = True
        self.root.attributes("-topmost", True)
        self.msgbar.focus_set()

    def print(self, *args, **kwargs):
        text_print(self.chatbox, *args, **kwargs)

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
        self.room_lock.acquire()
        self.alive = False 
        self.root.destroy()
        self.room_lock.release()
        #if self.after:
            #self.root.after_cancel(self.after)

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
        chatroom.print(
            '%s    [%s]' % (echo_msg, username),
            tag='host')
        chatroom.msgbar.delete(0, tk.END)
    else:
        chatroom.print('Error, please send your message again.')
    return

def win_config_set(window):
    window.resizable(width=False, height=False)
    window.configure(
        background='#ffffff',
        relief='flat',
    )

def button_config_set(button, command):
    button.configure(
        borderwidth = 0,
        background='#666666',
        foreground='#dddddd',
        font = ('Times', 12, 'normal'),
        relief = 'flat',
        command = command,
    )
def text_config_set(element, h=15):
    element.configure(
        borderwidth = 0,
        state = 'disabled',
        padx = 0,
        pady = 15,
        spacing1 = 6,
        spacing3 = 6,
        font = ('Times', 12, 'normal'),
        background = '#ffffff',
        foreground = '#444444',
        height = h,
        width = 45,
        relief='flat',
    )
    element.tag_configure(
        'start', 
        spacing1 = element['spacing1'],
        wrap='none',
        justify='center',
    )
    element.tag_configure(
        'end',
        spacing3 = element['spacing1'],
        wrap='none',
        justify='center',
    )
    element.tag_configure(
        'history', 
        foreground='#555555',
        background='#dddddd',
    )
    element.tag_configure(
        'file', 
        foreground='#dddddd',
        background='#444444',
    )
    element.tag_configure(
        'title',
        font = ('Times', 14, 'bold'),
    )
    element.tag_configure(
        'host', 
        justify='right',
    )
    element.tag_configure(
        'guest', 
        justify='left',
    )

def text_print(element, msg, end='\n', tag=None):
    element.configure(state='normal')
    if type(msg) == bytes:
        msg = msg.decode()
    if tag:
        element.insert('end', '  '+msg+'  '+end, tag)
    else:
        element.insert('end', '  '+msg+'  '+end)
    element.see('end')
    element.configure(state='disabled')



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
