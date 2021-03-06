NULL = bytes([0x00])

### Client request
REGISTER_REQUEST = bytes([0x01])
LOGIN_REQUEST = bytes([0x02])
LIST_REQUEST = bytes([0x03])
DISCON_REQUEST = bytes([0x04])
LOGOUT_REQUEST = bytes([0x05])
RSOCK_INIT = bytes([0x07])

### Server response
REQUEST_FIN = bytes([0x01])
LOGIN_SUCCEED = bytes([0x02])
LOGOUT_SUCCEED = bytes([0x04])
HISTORY_END = bytes([0x05])

### Both used (client to another client, via server)
# [code][peer username]\n[msg]

MSG_REQUEST = bytes([0x80]) # [msg] = user send msg
TRANSFER_REQUEST = bytes([0x83]) # [msg] = filename

TRANSFER_ACCEPT = bytes([0x85])
# C2S: [msg] = filename
# S2C: [msg] = [peer ip]:[peer port]

TRANSFER_DENY = bytes([0x86]) # [msg] = filename

### Both used
HISTORY_REQUEST = bytes([0x87])
