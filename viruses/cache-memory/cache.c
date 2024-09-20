#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef SIZE
// 32 MB array size, larger than most LLC caches
#   define SIZE	(32 * 1024 * 1024) 
#endif

#ifndef STRIDE
// Stride size to skip over cache lines
#   define STRIDE	64 
#endif

int main() {
    int *array = malloc(SIZE * sizeof(int));
    int sum = 0;
    clock_t start, end;

    // Initialize the array
    for (int i = 0; i < SIZE; i++) {
        array[i] = i;
    }

    start = clock();

    // Access array elements with a large stride, trashing the cache
    for (int i = 0; i < SIZE; i += STRIDE) {
        sum += array[i];
    }

    end = clock();

    printf("Sum: %d, Time: %f seconds\n", sum, (double)(end - start) / CLOCKS_PER_SEC);

    free(array);
    return 0;
}
