USERS_DB_PATH = "./users.db"
PASSWORD_SALT = "CNLINE"
PORT = 16666
SERVER_IP = "0.0.0.0"

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
