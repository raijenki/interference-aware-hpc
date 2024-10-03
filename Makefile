CC = gcc
CXX = g++
MPICC = mpicc
MPICXX = mpicxx
CFLAGS = -O2 -fopenmp -DOPENMP
LDFLAGS = -lm

all: minife.x stream_c.exe xsbench mt-dgemm memory

stream_c.exe: 
	$(CC) $(CFLAGS) -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=500 apps/stream/stream.c -o apps/stream/stream_c

mt-dgemm:
	$(CXX) $(CFLAGS) -std=c++11 -ffast-math -mavx2 -fopenmp -DUSE_CBLAS -o viruses/cpu/mt-dgemm viruses/cpu/mt-dgemm.c -lopenblas

memory:
	$(CC) $(CFLAGS) -DSIZE=33554432 -DSTRIDE=64 viruses/cache-memory/cache.c -o viruses/cache-memory/cache
	$(CC) $(CFLAGS) -DSIZE=33554432 -ITER=10000000 viruses/cache-memory/memory.c -o viruses/cache-memory/memory

# This is for miniMD
source_xsbench = \
apps/xsbench/Main.c \
apps/xsbench/io.c \
apps/xsbench/Simulation.c \
apps/xsbench/GridInit.c \
apps/xsbench/XSutils.c \
apps/xsbench/Materials.c

obj_xsbench = \
apps/xsbench/Main.o \
apps/xsbench/io.o \
apps/xsbench/Simulation.o \
apps/xsbench/GridInit.o \
apps/xsbench/XSutils.o \
apps/xsbench/Materials.o

xsbench: $(obj_xsbench) apps/xsbench/XSbench_header.h
	$(CC) $(CFLAGS) $(obj_xsbench) -o apps/xsbench/$@ $(LDFLAGS)

apps/xsbench/%.o: apps/xsbench/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# This is for miniFE
MFE_CPPFLAGS = -I. -Iapps/minife/utils -Iapps/minife/fem $(MINIFE_TYPES) \s
	$(MINIFE_MATRIX_TYPE) \
	-DHAVE_MPI -DMPICH_IGNORE_CXX_SEEK \
	-DMINIFE_REPORT_RUSAGE

MFE_OBJS = \
	apps/minife/src/BoxPartition.o \
	apps/minife/src/YAML_Doc.o \
	apps/minife/src/YAML_Element.o

MFE_UTIL_OBJS = \
	apps/minife/src/param_utils.o \
	apps/minife/src/utils.o \
	apps/minife/src/mytimer.o

MFE_MAIN_OBJ = \
	apps/minife/src/main.o

vpath %.cpp apps/minife/utils

miniFE.x:common_files $(MFE_MAIN_OBJ) $(MFE_OBJS) $(MFE_UTIL_OBJS) apps/minife/src/*.hpp generate_info
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(MAIN_OBJ) $(OBJS) $(UTIL_OBJS) $(OPTIONAL_OBJS) -o miniFE.x $(LDFLAGS) $(OPTIONAL_LIBS) $(LIBS)

common_files:
	.apps/minife/src/get_common_files

generate_info:
	.apps/minife/src/generate_info_header "$(CXX)" "$(CXXFLAGS)" "miniFE" "MINIFE"

apps/minife/src/%.o:apps/minife/src/%.cpp apps/minife/src/*.hpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -DMINIFE_INFO=$(MINIFE_INFO) -DMINIFE_KERNELS=$(MINIFE_KERNELS) -c $<

apps/minife/src/%.o:apps/minife/src/%.c apps/minife/src/*.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $<


clean:
	rm -f apps/stream/stream_c apps/stream/stream.c*.o viruses/cpu/mt-dgemm*.o viruses/cache-memory/cache*.o viruses/cache-memory/memory*.o