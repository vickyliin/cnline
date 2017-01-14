from util import *

def file_recver(port, chatroom, filename):
    # filename for display, need not contain path
    filepath = None
    while not filepath:
        filepath = tkfile.asksaveasfilename(
            filetypes=[('All files', '*')],
            title=filename, 
            initialfile=filename,
        )
    chatroom.print(
        'Receiving file %s from %s, using port %d' % \
        (filename, chatroom.guest, port),
        tag = 'file'
    )
    # create a server with port=port to recv file
    process = subprocess.run(['../file_recv', '%s' % port, filepath])
    print(process)
    if process.returncode == 1:
        chatroom.print( 'File %s received.' % filename,
            tag = 'file')
    else:
        chatroom.print( 'Error occurred during file %s transmission.' % filename,
            tag = 'file')

    chatroom.fileports.put(port)
    return

def file_sender(addr, chatroom, filename):
    # filename should contain path
    ip, port = addr.split(':')
    chatroom.print(
        'Sending file %s to %s' % \
        (basename(filename), chatroom.guest),
        tag='file'
    )
    # connect to sender with ip=ip, port=port and then
    # transfer file with filename
    print('File: %s\n IP: %s' % (filename,ip) )
    process = subprocess.run(['../file_send', ip, port, filename])
    print(process)
    if process.returncode == 1:
        chatroom.print( 'File %s sended.' % basename(filename) , tag='file')
    else:
        chatroom.print( 'Error occurred during file %s transmission.' % filename , tag='file')
    return

def recv_file(chatroom, filename):
    # do when recv a file request from server
    chatroom.root.protocol("WM_DELETE_WINDOW", lambda x=1: x)
    sender = chatroom.guest
    
    try:
        port = chatroom.fileports.get()
    except queue.Empty:
        chatroom.print(
            'You miss a file %s from %s ' % (filename,sender) +
            'because the MAX amount of file receive' +
            ' (%d) had been reached.' % MAX_TRANSFER_AMT,
            tag = 'file'
        )
        chatroom.send(TRANSFER_DENY)
        chatroom.recv()
        return

    accept = tkbox.askokcancel(
        'file from %s' % sender,
        'Do you want to accept file %s from %s?' % \
            (filename, sender)
    )
    if accept == True:

        # send the picked port to server 
        # the server will then pass it to the sender
        chatroom.send(TRANSFER_ACCEPT, port)
        chatroom.recv()

        file_recver(port, chatroom, filename)
    else:
        chatroom.send(TRANSFER_DENY)
        chatroom.recv()
        chatroom.print('You just rejected a file from %s.' % chatroom.guest, tag='file')
    chatroom.root.protocol("WM_DELETE_WINDOW", chatroom.close)

def req_file(chatroom):
    # do when click the file button
    chatroom.root.protocol("WM_DELETE_WINDOW", lambda x=1: x)
    filename = tkfile.askopenfilename()
    if not filename:
        # user cancel the file browser
        return
    chk = tkbox.askokcancel(
        'File transfer',
        'Do you want to transfer file %s to %s?' % \
            (basename(filename), chatroom.guest)
    )
    if chk:
        chatroom.send(TRANSFER_REQUEST, basename(filename))
        server_msg = chatroom.recv()
        code, msg = server_msg[:1], server_msg[1:]
        if code == TRANSFER_ACCEPT:
            addr = msg.decode() # ip:port
            file_sender(addr, chatroom, filename)
        elif code == TRANSFER_DENY:
            chatroom.print(msg, tag='file')
    chatroom.root.protocol("WM_DELETE_WINDOW", chatroom.close)
    return

