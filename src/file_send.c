#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/select.h>
#include <time.h>
#include <sys/time.h>
#define ERR_EXIT(a) { perror(a); exit(0); }
#define read_lock(fd, offset, whence, len) \
	            lock_reg((fd), F_SETLK, F_RDLCK, (offset), (whence), (len))
#define readw_lock(fd, offset, whence, len) \
	            lock_reg((fd), F_SETLKW, F_RDLCK, (offset), (whence), (len))
#define write_lock(fd, offset, whence, len) \
	            lock_reg((fd), F_SETLK, F_WRLCK, (offset), (whence), (len))
#define writew_lock(fd, offset, whence, len) \
	            lock_reg((fd), F_SETLKW, F_WRLCK, (offset), (whence), (len))
#define un_lock(fd, offset, whence, len) \
	            lock_reg((fd), F_SETLK, F_UNLCK, (offset), (whence), (len))
const int timeout=10;

int lock_reg(int fd, int cmd, int type, off_t offset, int whence, off_t len)
{
    struct flock lock;
    lock.l_type = type;     /* F_RDLCK, F_WRLCK, F_UNLCK */
    lock.l_start = offset;  /* byte offset, relative to l_whence */
    lock.l_whence = whence; /* SEEK_SET, SEEK_CUR, SEEK_END */
    lock.l_len = len;       /* #bytes (0 means to EOF) */
    return(fcntl(fd, cmd, &lock));
}
void ERR()
{
    fprintf(stderr,"jizz\n");
}
typedef struct {
    char hostname[512];  // server's hostname
    unsigned short port;  // port to listen
    int fd;  // fd to wait for a new connection
} server;

typedef struct {
    int fd;
    struct sockaddr_in addr;
    int finish;
    char msg[256];
    char host[256];
    unsigned short port;  // port to listen
} client;

void hosttoip(char* host,char *ip)
{
    struct hostent *he;
    struct in_addr **addr_list;
    int i;
    he=gethostbyname(host);
    addr_list = (struct in_addr **) he->h_addr_list;
    for(i=0;addr_list[i]!=NULL;i++)
    {
	strcpy(ip,inet_ntoa(*addr_list[i]));
	return;
    }
}

typedef struct {
    char host[512];  // client's host
    int conn_fd;  // fd to talk with client
    char buf[512];  // data sent by/to client
    size_t buf_len;  // bytes used by buf
    // you don't need to change this.
    int wait_for_write;  // used by handle_read to know if the header is read or not.
} request;

client cli;
server svr;  // server
int maxfd;  // size of open file descriptor table, size of request list


// Forwards

static void init_client(char* ip,int port);
// initailize a server, exit for error

// return 0: socket ended, request done.
// return 1: success, message (without header) got this time is in reqP->buf with reqP->buf_len bytes. read more until got <= 0.
// It's guaranteed that the header would be correctly set after the first read.
// error code:
// -1: client connection error

// parameter: /send ip port file
int main(int argc, char** argv) {
    int i,j, num=0,mx=0,ret,tar,legal,end,n=0,t=1000,now[1024];
    struct sockaddr_in cliaddr;  
    int clilen;
    fd_set readset,readyset;
    FD_ZERO(&readset);
    int conn_fd;  // fd for a new connection with client
    int file_fd;  // fd for file that we open for reading
    char buf[1024];
    char *hostname,ip[32];
    int port;
    int buf_len;
    struct timeval t1[1024],t_now;
    if(argc!=4)
    {
	fprintf(stderr,"usage: %s [ip] [port] [filename]\n",argv[0]);
	return -1;
    }
    port=atoi(argv[2]);
    hosttoip(argv[1],ip);
    int fd;
    char checksum=1;
    init_client(ip,port);
    fd=open(argv[3],O_RDONLY);
    if(fd<0) perror("Open Error"); 
    int byte;
    while((byte=read(fd,buf,sizeof(buf)))!=0)
    {
	write(cli.fd,buf,byte);
    }
    close(cli.fd);
    init_client(ip,port);
    checksum=0;
    int bit=read(cli.fd,&checksum,sizeof(char));
    fd=open(argv[3],O_RDONLY);
    if(fd<0) perror("Open Error"); 
    char tmp;
    while(read(fd,&tmp,sizeof(char))!=0)checksum=checksum^tmp;
    if(checksum!=0)return 0;
    close(fd);
    close(cli.fd);
    return 1;
}


#include <fcntl.h>


static void init_client(char* ip,int port) {

    int flags;
    gethostname(cli.host, sizeof(cli.host));
    cli.port =port;

    cli.fd = socket(AF_INET, SOCK_STREAM, 0);
    if ( cli.fd < 0) ERR_EXIT("socket");
    bzero(&cli.addr, sizeof(cli.addr));
    cli.addr.sin_family = AF_INET;
    cli.addr.sin_addr.s_addr = inet_addr(ip);
    cli.addr.sin_port = htons(port);
    int cnt=0;
    while(connect(cli.fd, (struct sockaddr *) &cli.addr,sizeof(cli.addr))<0)
    {
	cnt++;
	if(cnt> timeout * 10 )
	{
	    fprintf(stderr,"Connection Timeout!\n");
	    exit(0);
	}
	usleep(100000);
    }
}


