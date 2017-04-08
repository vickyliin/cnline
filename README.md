# CNLine
CNLine is an instant messaging application which supports offline chat and file transfer, written in Python 3, C, Tcl/Tk and SQLite

# setup
## server
First, configure `config.py`, which contains following information

| variable | meaning|
|-|-|
|USERS_DB_PATH | path of the SQLite database |
|PASSWORD_SALT | salt for password hashing |
|PORT | the port that server listen on |
|FILE_PORT | port for file transfer handshaking |
|SERVER_IP | The ip that server socket binds to |

then execute
```
$ ./setup_sql.py
```
to generate the SQLite database.
Also, please check the NAT and firewall settings for the environment and do the port forwarding if necessary.

## client
run
```
$ make
```
this will generate the `file_recv` and `file_send` binary, which are the file transfer module called by client.

# Usage
## server
To start the server, execute
```
$ ./server.py
```
Press `^C` to shutdown the server.

## client
run
```
$ ./client.py
```
