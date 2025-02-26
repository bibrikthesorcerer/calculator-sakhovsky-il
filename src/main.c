#include "calculator.h"

int main(int argc, char* argv[])
{
    char buffer[MAX_BUFFER_SIZE];
    int len = 0;
    int space_left = sizeof(buffer);

    if (argc > 1 && strcmp(argv[1], "--float") == 0) {
        set_mode(FLOAT_MODE);
    }

    while (fgets(buffer + len, space_left, stdin)) {
        len += strlen(buffer + len);
        space_left -= len;
    }
    validate_and_strip_input(buffer);

    NumberType result = calculate_expression(buffer);

    if (get_mode() == FLOAT_MODE) {
        printf("%.4f\n", result.floatValue);
    } else {
        printf("%ld\n", result.intValue);
    }

    return 0;
}
