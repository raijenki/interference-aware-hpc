CC = gcc
CFLAGS = -O2 -fopenmp -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=500

all: stream_c.exe

stream_c.exe: 
	$(CC) $(CFLAGS) -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=500 apps/stream/stream.c -o apps/stream/stream_c

clean:
	rm -f apps/stream/stream_c apps/stream/stream.c*.o