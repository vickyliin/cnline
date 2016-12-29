# Client request
REGISTER_REQUEST = bytes([0x01])
LOGIN_REQUEST = bytes([0x02])
LIST_REQUEST = bytes([0x03])
DISCON_REQUEST = bytes([0x04])
LOGOUT_REQUEST = bytes([0x05])

# Server response
REQUEST_FIN = bytes([0x01])
LOGIN_SUCCEED = bytes([0x02])
TALK_SUCCEED = bytes([0x03])
LOGOUT_SUCCEED = bytes([0x04])

# Both used (client to another client, via server)
MSG_REQUEST = bytes([0x80])
TALK_REQUEST = bytes([0x81])
LEAVE_REQUEST = bytes([0x82])
TRANSFER_REQUEST = bytes([0x83])
TRANSFER_ACCEPT = bytes([0x85])
TRANSFER_DENY = bytes([0x86])
