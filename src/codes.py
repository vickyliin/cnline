REQUEST_CODE = dict(
        register = 1,
        login = 2,
        ls = 3,
        talk = 4,
        msg = 5,
        disconnect = 6,
        transfer = 7, 
        logout = 8, 
        leave = 9, )

SERVER_CODE = dict(
        login_succeed = 1,
        req_end = 2,
        talk_req_succeed = 3, 
        logout_succeed = 4, )

REGISTER_REQUEST = bytes([0x01])
LOGIN_REQUEST = bytes([0x02])
LIST_REQUEST = bytes([0x03])
TALK_REQUEST = bytes([0x04])
MSG_REQUEST = bytes([0x05])
DISCON_REQUEST = bytes([0x06])
TRANS_REQUEST = bytes([0x07])
LOGOUT_REQUEST = bytes([0x08])
LEAVE_REQUEST = bytes([0x09])

LOGIN_SUCCEED = bytes([0x01])
REQUEST_FIN = bytes([0x02])
TALK_SUCCEED = bytes([0x03])
LOGOUT_SUCCEED = bytes([0x04])
