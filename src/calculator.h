#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

#define MAX_BUFFER_SIZE 1024
#define FLOAT_PRECISION 1e-4

typedef enum { INT_MODE, FLOAT_MODE } Mode;

// union lets us interpret one piece of a memory as a different types
// they are both take 8 bytes in UNIX
typedef union {
    long intValue;
    double floatValue;
} NumberType;

int set_global_pos(int new_pos);

int get_global_pos();

Mode set_mode(Mode new_mode);

Mode get_mode();

NumberType calculate_expression(char* buffer);

int is_valid_char(char c);

void validate_and_strip_input(char* buffer);

NumberType get_operand(char* buffer);

NumberType get_product(char* buffer);
