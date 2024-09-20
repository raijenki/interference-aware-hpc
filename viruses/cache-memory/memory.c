#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef SIZE
// 512 MB array size, larger than typical RAM cache
#   define SIZE (512 * 1024 * 1024) 
#endif

#ifndef ITER
#   define ITER 10000000
#endif

int main() {
    int *array = malloc(SIZE * sizeof(int));
    int sum = 0;
    clock_t start, end;

    // Seed the random number generator
    srand(time(NULL));

    start = clock();

    // Randomly access elements of a large array, trashing memory
    for (int i = 0; i < ITER; i++) {
        int index = rand() % SIZE;
        sum += array[index];
    }

    end = clock();

    printf("Sum: %d, Time: %f seconds\n", sum, (double)(end - start) / CLOCKS_PER_SEC);

    free(array);
    return 0;
}
