#include <stdio.h>

int main() {
    printf("Hello FreeRTOS!\n");
    return 0;
}

// MISRA violation: missing function comment
int add(int a, int b) {
    return a + b;
}
