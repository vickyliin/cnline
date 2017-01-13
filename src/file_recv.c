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
const int TIMEOUT=10;
int lock_reg(int fd, int cmd, int type, off_t offset, int whence, off_t len)
{
    struct flock lock;
    lock.l_type = type;     /* F_RDLCK, F_WRLCK, F_UNLCK */
    lock.l_start = offset;  /* byte offset, relative to l_whence */
    lock.l_whence = whence; /* SEEK_SET, SEEK_CUR, SEEK_END */
    lock.l_len = len;       /* #bytes (0 means to EOF) */
    return(fcntl(fd, cmd, &lock));
}
typedef struct {
    char hostname[512];  // server's hostname
    unsigned short port;  // port to listen
    int listen_fd;  // fd to wait for a new connection
} server;

void ERR()
{
    fprintf(stderr,"jizz\n");
}
typedef struct {
    int fd;
    struct sockaddr_in addr;
    int finish;
    char msg[256];
    char host[256];
} client;


client cli;
server svr;  
int maxfd;



static void init_server(unsigned short port);

int main(int argc, char** argv) {
    int i,num=0;
    int clilen;
    char buf[1024],cmd[1024];
    fd_set readyset;
    if (argc != 3) {
        fprintf(stderr, "usage: %s [port] [filename]\n", argv[0]);
        exit(0);
    }
    init_server((unsigned short) atoi(argv[1]));
    struct timeval slice;
    int cnt=0;
    while (1) {
	cnt++;
	if(cnt>TIMEOUT*10)
	{
	    fprintf(stderr,"Connection Timeout!\n");
	    exit(0);
	}
        FD_ZERO(&readyset);
        FD_SET(svr.listen_fd,&readyset);
    	slice.tv_sec=0;
    	slice.tv_usec=100000ul;
	select(1024,&readyset,0,0,&slice);
	if(FD_ISSET(svr.listen_fd,&readyset))break;
    }
    clilen = sizeof(cli.addr);
    cli.fd = accept(svr.listen_fd, (struct sockaddr*)&cli.addr, (socklen_t*)&clilen);
    int byte,fd=open(argv[2],O_WRONLY | O_TRUNC | O_CREAT);
    while((byte=read(cli.fd,buf,sizeof(buf)))!=0)
    {
	write(fd,buf,byte);
    }
    close(cli.fd);
    clilen = sizeof(cli.addr);
    cli.fd = accept(svr.listen_fd, (struct sockaddr*)&cli.addr, (socklen_t*)&clilen);
    char checksum=0;
    sprintf(cmd,"chmod 0700 %s",argv[2]);
    system(cmd);
    fd=open(argv[2],O_RDONLY);
    if(fd<0) perror("Open Error"); 
    char tmp;
    while(read(fd,&tmp,sizeof(char))!=0)checksum=checksum^tmp;
    write(cli.fd,&checksum,sizeof(char));
    read(cli.fd,&checksum,sizeof(char));
    if(checksum!=0)
    {
	remove(argv[2]);
	return 0;
    }
    close(fd);
    close(cli.fd);
    return 1;
}


#include <fcntl.h>


static void init_server(unsigned short port) {
    struct sockaddr_in servaddr;
    int tmp;

    gethostname(svr.hostname, sizeof(svr.hostname));
    svr.port = port;

    svr.listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (svr.listen_fd < 0) ERR_EXIT("socket");

    bzero(&servaddr, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    servaddr.sin_port = htons(port);
    tmp = 1;
    if (bind(svr.listen_fd, (struct sockaddr*)&servaddr, sizeof(servaddr)) < 0) {
        ERR_EXIT("bind");
    }
    if (listen(svr.listen_fd, 1024) < 0) {
        ERR_EXIT("listen");
    }
}
