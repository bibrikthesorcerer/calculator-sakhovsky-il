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

The work with this program is carried out using a server and a `GUI` that acts as a client in this program.

## Building on your machine

To build this program You need a **C compiler** such as [gcc](https://en.wikipedia.org/wiki/GNU_Compiler_Collection), [clang](https://en.wikipedia.org/wiki/Clang), etc.  
*(you can even use `zig cc` if you think you're cool enough)*

You'll also need `git`, `cmake` and `make` if you want to run unit tests

> [!IMPORTANT]
> To run this program on your device, you will need `docker compose`. If you want to run this program outside of docker, then you will need `redis`.

### Makefile
I've included **gcc-based Makefile** in repo, so you can use:
```bash
make all               # to build program (app.exe) and unit tests (unit-tests.exe)
make clean             # to clean build artifacts
make run-int           # to run app.exe
make run-float         # to run app.exe --float
make run-unit-test     # to run unit-tests.exe
make format            # to format .cpp .c .h files using WebKit style
make run-server        # to run docker compose for the server
make stop-server       # to stop docker compose for the server
make run-server-python # to run server
make run-gui           # to run client
```

## Running and using this program

You can run this program via **Makefile**. First, run the command
```bash
make run-server # to run docker compose for the server
```

Then, run the command
```bash
make run-gui    # to run client
```

The correct input, in the field intended for this in the `GUI`, contains **only**:
- `0-9`  digits
- `+`, `-`, `*`, `/` supported operations
- `(`, `)` parenthesis
- ` `, `\t`, `\n`, `\v`, `\f`, `\r` whitespaces

This program supports up to 1KiB of input data  
Program assumes that all numbers are non-negative

The program returns the result of calculations to the prepared table in the `GUI`.

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

## Use-case diagram of FSM operation

![alt text](https://github.com/bibrikthesorcerer/calculator-sakhovsky-il/blob/main/media/FSM.png?raw=true)

<p style="text-align: center;">Image 1. Use-case diagram of FSM operation</p>

## Demonstration of the server operation

The figures show the server operation scheme for a large number of clients.

Random requests of varying complexity were received on the server, among which requests containing an error were specially added to find out how this would affect the efficiency of the server.

![alt text](https://github.com/bibrikthesorcerer/calculator-sakhovsky-il/blob/main/media/40VU.png?raw=true)

<p style="text-align: center;">Image 2. The scheme of the server with 40 virtual users</p>

![alt text](https://github.com/bibrikthesorcerer/calculator-sakhovsky-il/blob/main/media/60VU.png?raw=true)

<p style="text-align: center;">Image 3. The scheme of the server with 60 virtual users</p>

![alt text](https://github.com/bibrikthesorcerer/calculator-sakhovsky-il/blob/main/media/80VU.png?raw=true)

<p style="text-align: center;">Image 4. The scheme of the server with 80 virtual users</p>

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
- python in the Makefile has been replaced with python3 for compatibility with Ubuntu.
- Fixed a bug when parsing float_mode from a POST request sent to the server.
- Fixed an error when processing arithmetic expressions ending with an operation.

### SAT-12

`Integration tests` have been added to verify the server's health, and the **Makefile** has been updated to perform both regular and server `integration tests`.

### SAT-14, SAT-15, SAT-16

A basic graphical interface with client-server interaction was implemented, namely:
- A button to send data to the server.
- Fields for entering arithmetic expressions and outputting the answer.
- Checkbox for float mode.

Some minor fixes have also been made.

### SAT-17, SAT-18

The following changes have been added:
- Basic validation of input data has been introduced.
- Introduced a 2-second delay of the GUI after sending the request.

### SAT-19, SAT-20, SAT-21

The following functionality has been added:
- Added a class that performs the role of FSM.
- Added a check for GUI connections to the server.
- Added Dockerfile support to Makefile for calculator program and server.

### SAT-23

The following changes have been made to the Makefile:
- Added GUI startup.
- The doker cleaning feature has been added to the clean command.
- A separate command has been issued to launch the python server.
- The run-server command launches docker and app.exe.
- Improved commands for working with the doсker.

### SAT-24

A `Django` application with a basic `DB` configuration has been added, which allows you to save the calculation history on the server.

### SAT-25, SAT-26, SAT-27, SAT-28

The following functionality has been implemented:
- The list of clients connected to the server.
- PUSH server model that allows sending data to all connected clients.
- Asynchronous server operation.
- Sending the calculation history when the client connects to the server for the first time.

### SAT-29, SAT-30

The following changes have been made:

- Added a data warehouse for the calculation history from the server in the GUI.
- Added WS client to provide convenient two-way communication between GUI and server.
- The client application has become modular and has been divided into subsections to ensure its continuous operation.

### SAT-32, SAT-33, SAT-34

The following changes have been made:
- Added Logging on server.
- Updated Makefile for correct launch of docker, server and GUI.
- Added the docker-compose setting.
- The working IP has been changed to 0.0.0.0.

### SAT-31, SAT-37, SAT-39

The following work was performed: 
- Testing was conducted to identify errors and malfunctions in the program.
- Fixed a bug that led to an endless loop of requests to the server in order to obtain the calculation result.
- Improved the system for reconnecting the client to the server and checking the server health at the moment.

### SAT-40

The migration command was added to the **Makefile** to start the server.

### SAT-36

`Queues` were removed from the program and errors that periodically occurred at the end of the program were fixed.

### SAT-38

A data validation system has been added to the server.

### SAT-41

An error related to spaces in arithmetic expressions entered in the `GUI` has been fixed.

### SAT-42

An error has been fixed that occurs when the program is running when the dependent parts of the program were running in the wrong order.
