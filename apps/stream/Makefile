CC = gcc
CFLAGS = -O2 -fopenmp -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=500

all: stream_c.exe

stream_c.exe: stream.c
	$(CC) $(CFLAGS) stream.c -o stream_c

clean:
	rm -f stream_c *.o