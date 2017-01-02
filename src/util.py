from threading import Thread, Lock
import tkinter as tk
import tkinter.messagebox as tkbox
import tkinter.filedialog as tkfile
import socket
from time import sleep
from os.path import isfile, basename
import queue

import config
from codes import *

MAX_RECV_LEN = 4096
MAX_TALK_AMT = 20

def thpack(function, *args, name = None, **kwargs):
    # pack the fuction with thread and change the input arguments
    def pack(*e):
        th = Thread(
            target = function,
            args = args,
            kwargs = kwargs,
            name = name,
            )
        th.start()
    return pack
