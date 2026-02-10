#include <stdio.h>

int main() {
    printf("Hello FreeRTOS!\n");
    return 0;
}

// MISRA violation: missing function comment
int add(int a, int b) {
    return a + b;
}
// Trigger workflow
// Retry with updated config
// Retry after IAM propagation delay
// Retry with updated IAM policy
// Retry with updated IAM policy
// Test without filesystem MCP
