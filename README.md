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

This program is also capable of running a server that can process certain types of POST requests.

## Building on your machine

To build this program You need a **C compiler** such as [gcc](https://en.wikipedia.org/wiki/GNU_Compiler_Collection), [clang](https://en.wikipedia.org/wiki/Clang), etc.  
*(you can even use `zig cc` if you think you're cool enough)*

You'll also need `git`, `cmake` and `make` if you want to run unit tests

All sources are in `src/` folder so you can compile them yourself or use **Makefile**

### Makefile
I've included **gcc-based Makefile** in repo, so you can use:
```bash
make all            # to build program (app.exe) and unit tests (unit-tests.exe)
make clean          # to clean build artifacts
make run-int        # to run app.exe
make run-float      # to run app.exe --float
make run-unit-test  # to run unit-tests.exe
make format         # to format .cpp .c .h files using WebKit style
make run-server     # to run the calc_server.py
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

### 3. **Input Handling**  
Before calculation, program validates and sanitizes input using `validate_and_strip_input()`.  
This function removes whitespaces and checks for valid input characters using `is_valid_char()` function.

### 4. **Error Handling**  
I've added exit codes to the app.  
| Error situation  | Exit code |
| ---------------- | --------- |
| Division by zero in `INT_MODE`  | 1  |
| Division by a number less than `0.0001` in `FLOAT_MODE`  | 2  |
| Invalid input symbol | 3 |
| Not closed parenthesis | 4 |

## Repository Update Report

### SAT-1

The following functions have been implemented:
- Functionality for creating (launching) a server.
- Functionality for receiving POST requests by the server.
- The ability to run the server at a pre-specified address and port.
- Returning a base 200 response to any incoming POST request.

### SAT-2

`Content-type`, `query`, and `requestBody` verification has been added.

### SAT-3

Basic routing has been added, which includes a `/calc` endpoint and a `404` handler.

### SAT-4

The following functionality has been added:
- The class that is responsible for launching the calculator application.
- Interaction between the server and the written class.

The server uses the class to run the application using the received input data.

### SAT-5

Functionality has been added for checking and, if necessary, compiling the application.

### SAT-6

The **Makefile** has been updated to add the `"run-server"` command to run the server. (Thanks, Cap)

### SAT-9

Support for the `structlog` module in venv has been added, and the `"run-server"` command has been wrapped in venv.

### SAT-7

Console logging using structlog has been added, which includes:
- Logging levels (INFO, ERROR, etc.).
- Information about the time and date of logging in the ISO-8601 format.
- Information about unhandled exceptions.

### SAT-8

Parallel logging in `JSON` format has been added. The received logs are written to a file with the *`.log`* extension.

### SAT-10

The `venv` and the `run-server` command in the **Makefile** were fixed.

### SAT-11

The following changes have been made:
- python in the Makefile has been replaced with python3 for compatibility with Ubuntu
- Fixed a bug when parsing float_mode from a POST request sent to the server
- Fixed an error when processing arithmetic expressions ending with an operation

### SAT-12

`Integration tests` have been added to verify the server's health, and the **Makefile** has been updated to perform both regular and server `integration tests`.