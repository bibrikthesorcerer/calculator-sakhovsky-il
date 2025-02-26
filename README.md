# calculator-sakhovsky-il

## About (What had been done)

This program is capable to **parse and calculate arithmetic expressions**.  

Supported operations: `+`, `-`, `*`, `/`.  
Program also supports parethesis: `(`, `)`.

There are two calculation modes available - `INT_MODE` and `FLOAT_MODE`.  
Mode influences type of intermediate calculations and given result.  
E.g.:
```
INT_MODE:
    5/2 = 2

FLOAT_MODE:
    5/2 = 2.5
```

## Building on your machine

To build this program You need a **C compiler** such as [gcc](https://en.wikipedia.org/wiki/GNU_Compiler_Collection), [clang](https://en.wikipedia.org/wiki/Clang), etc.  
*(you can even use `zig cc` if you think you're cool enough)*

From that, **building is straightforward** - navigate into directory with `main.c`, compile and run it.

For example, you can compile and run this program using `gcc` **like this**:
```bash
gcc main.c -o <OUTPUT_FILE>
./<OUTPUT_FILE>
```

### Makefile
I've included **gcc-based Makefile** in repo, so you can use:
```bash
make all            # to build program (app.exe) and unit tests (unit-tests.exe)
make clean          # to clean build artifacts
make run-int        # to run app.exe
make run-float      # to run app.exe --float
make run-unit-test  # to run unit-tests.exe
make format         # to format .cpp .c .h files using WebKit style
```
All build artifacts are stored in `build/` directory

## Running and using this program

You can run this program via Makefile
```bash
make run-int    # to run in INT_MODE
make run-float  # to run in FLOAT_MODE
```

Or straight from built .exe file
```bash
./build/app.exe [--float]
```

> [!IMPORTANT]
> - Program expects user input in `stdin` until `EOF` is met  
> - **To end input, type `EOF` symbol** *(use Ctrl+D in linux terminal)*
> - You can also pipe input to program using `echo "2+3" | build/app.exe`

Input is a string, containing **only**:
- `0-9`  digits
- `+`, `-`, `*`, `/` supported operations
- `(`, `)` parenthesis
- ` `, `\t`, `\n`, `\v`, `\f`, `\r` whitespaces

This program supports up to 1KiB of input data  
Program assumes that all numbers are non-negative

Program outputs single number representing evaluated expression in `stdout`

## How it's made

### 1. **Recursive Descent Parser**  
I've used [recursive descent parser](https://en.wikipedia.org/wiki/Recursive_descent_parser?useskin=vector) to calculate inputted arithmetic expression.  

Basically, all supported arithmetic expressions can be derivated from this grammar:  

`E = Expression, P = Product, O = Operand`
```
1. E  → P ((+ | -)+ P)*
2. P  → O ((* | /)+ O)*
3. O  → NUMBER 
4. O  → ( expression )
```

I've implemented a function for derivation of every rule
- `calculate_expression()`: Handles addition/subtraction **Rule 1**
- `get_product()`: Handles multiplication/division **Rule 2**
- `get_operand()`: Processes numbers and parentheses **Rules 3,**

### 2. **Number Representation**  
Im using union for working with multiple types inside one allocated memory
```c
typedef union {
    long intValue;
    double floatValue;
} NumberType;
```
**App is capable to calculate in INT and FLOAT modes.**  
I've added mode managing with `set_mode()/get_mode()`

3. **Input Handling**  
Before calculation, program validates and sanitizes input using `validate_and_strip_input()`.  
This function removes whitespaces and checks for valid input characters using `is_valid_char()` function.

4. **Error Handling**  
I've added exit codes to the app.
| Error situation  | Exit code |
| ---------------- | --------- |
| Division by zero in `INT_MODE`  | 1  |
| Division by a number less than<br>`$10^-4$`in `FLOAT_MODE`  | 2  |
| Invalid input symbol | 3 |
| Not closed parenthesis | 4 |