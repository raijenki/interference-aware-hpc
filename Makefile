CC = gcc
CFLAGS = -O2 -fopenmp

all: stream_c.exe mt-dgemm

stream_c.exe: 
	$(CC) $(CFLAGS) -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=500 apps/stream/stream.c -o apps/stream/stream_c

mt-dgemm: mt-dgemm.c
	$(CC) $(CFLAGS) -std=c++11 -ffast-math -mavx2 -fopenmp -DUSE_CBLAS -o viruses/cpu/mt-dgemm viruses/cpu/mt-dgemm.c -lopenblas

clean:
	rm -f apps/stream/stream_c apps/stream/stream.c*.o