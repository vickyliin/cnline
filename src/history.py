from util import *

def req_hist(chatroom):
    # do when click the History button
    # TODO request talk history and display on the chatbox

    n = tksd.askinteger('History', 'Enter the number:')
    if n:
        chatroom.send(HISTORY_REQUEST, n)
        chatroom.recv()
    return
