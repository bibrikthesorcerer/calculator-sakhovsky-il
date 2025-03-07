#include "calculator.h"

static int global_pos = 0;
static Mode currentMode = INT_MODE;

int set_global_pos(int new_pos)
{
    global_pos = new_pos;
    return global_pos;
}

int get_global_pos() { return global_pos; }

Mode set_mode(Mode new_mode)
{
    currentMode = new_mode;
    return currentMode;
}

Mode get_mode() { return currentMode; }

int is_valid_char(char c) { return isdigit(c) || strchr("()*+-/", c) || isspace(c); }

void validate_and_strip_input(char* buffer)
{
    char* old = buffer; // iterator, goes all way through buffer
    char* new = buffer; // iterator, copies non-whitespaces in buffer
    int parenthesis = 0;
    int prev_char_was_digit = 0;
    int space_count = 0;
    int prev_char_was_operator = 0;    // Track if the previous character was an operator
    int prev_char_was_open_paren = 0;  // Track if the previous character was an opening parenthesis
    int prev_char_was_close_paren = 0; // Track if the previous character was a closing parenthesis

    for (; *old != 0; ++old) {
        if (!is_valid_char(*old)) exit(3);

        if (isspace(*old)) {
            space_count++;
            continue;
        }

        if (isdigit(*old)) {
            if (prev_char_was_digit && space_count > 0) {
                // Two numbers separated by spaces without an operator
                exit(3);
            }
            prev_char_was_digit = 1;
        } else {
            prev_char_was_digit = 0;
        }

        space_count = 0;

        if (strchr("+-*/", *old)) {
            // Check for invalid unary operators
            if ((prev_char_was_operator || prev_char_was_open_paren || new == buffer) && !prev_char_was_close_paren) {
                exit(3);
            }
            prev_char_was_operator = 1;
        } else {
            prev_char_was_operator = 0;
        }

        if (*old == '(') {
            ++parenthesis;
            prev_char_was_open_paren = 1;
            prev_char_was_close_paren = 0;
        } else if (*old == ')') {
            --parenthesis;
            prev_char_was_close_paren = 1;
            prev_char_was_open_paren = 0;
        } else {
            prev_char_was_open_paren = 0;
            prev_char_was_close_paren = 0;
        }

        *new = *old; // copy non-spaces
        ++new;       // move iter
    }
    *new = 0; // add \0

    if (parenthesis != 0) exit(4);
    if (prev_char_was_operator) exit(3);
}

// retrieves either next number or result of calculated expression in parenthesis
NumberType get_operand(char* buffer)
{
    NumberType num;
    // if parenthesis met, calculate sub-expression and return its value
    if (buffer[global_pos] == ')') exit(4);
    if (buffer[global_pos] == '(') {
        global_pos++;
        num = calculate_expression(buffer);
        global_pos++;
        return num;
    }
    // construct a number if no parenthesis met
    if (currentMode == INT_MODE) {
        num.intValue = 0;
        while (isdigit(buffer[global_pos])) {
            num.intValue = num.intValue * 10 + (buffer[global_pos++] - '0');
        }
    } else { // FLOAT_MODE
        num.floatValue = 0.0;
        while (isdigit(buffer[global_pos])) {
            num.floatValue = num.floatValue * 10 + (buffer[global_pos++] - '0');
        }
    }

    return num;
}

// returns product of subsequent multiplications(divisions)
NumberType get_product(char* buffer)
{
    // get first operand considering parenthesis
    NumberType res = get_operand(buffer);
    // multiply while there are multiplication symbols
    while (buffer[global_pos] == '*' || buffer[global_pos] == '/') {
        char operation = buffer[global_pos];
        ++global_pos;
        NumberType x = get_operand(buffer);

        if (operation == '*') {
            if (currentMode == INT_MODE) {
                res.intValue *= x.intValue;
            } else {
                res.floatValue *= x.floatValue;
            }
        } else {
            if (currentMode == INT_MODE) {
                if (x.intValue == 0) exit(1);
                res.intValue /= x.intValue;
            } else {
                if (fabs(x.floatValue) < FLOAT_PRECISION) exit(2);
                res.floatValue /= x.floatValue;
            }
        }
    }
    return res;
}

NumberType calculate_expression(char* buffer)
{
    // get first operand considering multiplication
    NumberType res = get_product(buffer);
    // sum two values while there are sum symbols
    while (buffer[global_pos] == '+' || buffer[global_pos] == '-') {
        char operation = buffer[global_pos];
        ++global_pos;
        NumberType x = get_product(buffer);

        if (operation == '+') {
            if (currentMode == INT_MODE) {
                res.intValue += x.intValue;
            } else {
                res.floatValue += x.floatValue;
            }
        } else {
            if (currentMode == INT_MODE) {
                res.intValue -= x.intValue;
            } else {
                res.floatValue -= x.floatValue;
            }
        }
    }

    return res;
}