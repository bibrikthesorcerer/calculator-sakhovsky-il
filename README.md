# calculator-sakhovsky-il

## About

This program is capable to **parse and calculate arithmetic expressions**.  
Right now supported operations are: `+`, `-`, `*`, `/`.  
Program also supports parethesis: `(`, `)`.

## Building and running on your machine

To build this program You need a **C compiler** such as [gcc](https://en.wikipedia.org/wiki/GNU_Compiler_Collection), [clang](https://en.wikipedia.org/wiki/Clang), etc.  
*(you can even use `zig cc` if you think you're cool enough)*

From that, **building is straightforward** - navigate into directory with `main.c`, compile and run it.

For example, you can compile and run this program using `gcc` **like this**:
```bash
gcc main.c -o <OUTPUT_FILE>
./<OUTPUT_FILE>
```
I've included **gcc-based makefile** in repo, so you can use:
```bash
make                # to build the program using gcc, output is calculator.out
./calculator.out    # to run built program
make clean          # to clean build artifacts
```

## Using this program

> [!IMPORTANT]
> - Program expects user input in `stdin` until `EOF` is met  
> - **To end input, type `EOF` symbol** *(use Ctrl+D in linux terminal)*

Input is a string, containing **only**:
- `0-9`  digits
- `+`, `-`, `*`, `/` supported operations
- `(`, `)` parenthesis
- ` `, `\t`, `\n`, `\v`, `\f`, `\r` whitespaces

This program supports up to 1KiB of input data  
Program assumes that all numbers are non-negative

Program outputs single number representing evaluated expression in `stdout`