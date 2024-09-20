CC = gcc
CXX = g++
CFLAGS = -O2 -fopenmp

all: stream_c.exe mt-dgemm memory

stream_c.exe: 
	$(CC) $(CFLAGS) -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=500 apps/stream/stream.c -o apps/stream/stream_c

mt-dgemm:
	$(CXX) $(CFLAGS) -std=c++11 -ffast-math -mavx2 -fopenmp -DUSE_CBLAS -o viruses/cpu/mt-dgemm viruses/cpu/mt-dgemm.c -lopenblas

memory:
	$(CC) $(CFLAGS) -DSIZE=33554432 -DSTRIDE=64 viruses/cache-memory/cache.c -o viruses/cache-memory/cache
	$(CC) $(CFLAGS) -DSIZE=33554432 -ITER=10000000 viruses/cache-memory/memory.c -o viruses/cache-memory/memory

clean:
	rm -f apps/stream/stream_c apps/stream/stream.c*.o viruses/cpu/mt-dgemm*.o viruses/cache-memory/cache*.o viruses/cache-memory/memory*.o