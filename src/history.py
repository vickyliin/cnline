from util import *

def req_hist(chatroom):
    # do when click the History button
    # TODO request talk history and display on the chatbox
    chatroom.send(HISTORY_REQUEST, '10')
    chatroom.recv()
    return
