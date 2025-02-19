#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static int global_pos = 0;

int calculate_expression();

void exclude_whitespaces(char *buffer) {
    char *old = buffer; // iterator, goes all way through buffer
    char *new = buffer; // iterator, copies non-whitespaces in buffer
    for(; *old != 0; ++old){
        if(isspace(*old)) // skip spaces
            continue;

        *new = *old; // copy non-spaces
        ++new; // move iter
    }
    *new = 0; // add \0
}

// retrieves either next number or result of calculated expression in parenthesis
int get_operand(char *buffer) {
    // if parenthesis met, calculate sub-expression and return its value
    if (buffer[global_pos] == '(') {
        ++global_pos;
        int res = calculate_expression(buffer);
        ++global_pos;
        return res;
    }
    // construct a number if no parenthesis met
    int num = 0;
    char new_digit;
    while (isdigit(buffer[global_pos])){
        new_digit = buffer[global_pos];
        ++global_pos;
        num = num * 10 + (new_digit - '0');
    }
    return num;
}

// returns product of subsequent multiplications(divisions)
int get_product(char *buffer) {
    // get first operand considering parenthesis
    int res = get_operand(buffer);
    // multiply while there are multiplication symbols
    while (buffer[global_pos] == '*' || buffer[global_pos] == '/') {
        char operation = buffer[global_pos];
        ++global_pos;
        int x = get_operand(buffer);
        if (operation == '*')
            res *= x;
        else
            res /= x;
    }
    return res;
}


int calculate_expression(char *buffer) {
    // get first operand considering multiplication
    int res = get_product(buffer);
    // sum two values while there are sum symbols
    while (buffer[global_pos] == '+' || buffer[global_pos] == '-') {
        char operation = buffer[global_pos];
        ++global_pos;
        int x = get_product(buffer);
        if (operation == '+')
            res += x;
        else
            res -= x;
    }
    return res;
}

int main() {
    char buffer[1024];
    int len = 0;
    int space_left = sizeof(buffer);

    while(fgets(buffer + len, space_left, stdin)) {
        len += strlen(buffer + len);
        space_left -= len;
    }
    
    exclude_whitespaces(buffer);
    printf("%d\n", calculate_expression(buffer));
    return 0;
}