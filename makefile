trans:
	g++ src/file_send.c -o file_send
	g++ src/file_recv.c -o file_recv
clean:
	rm file_send file_recv
