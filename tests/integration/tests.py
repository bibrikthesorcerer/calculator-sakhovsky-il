import subprocess
import pytest
import os

def pytest_configure(config):
    if not os.path.isfile('./build/app.exe'):
        pytest.exit("Missing executable. Compile first!", returncode=1)

valid_cases = [
    # Integer mode tests
    ("2+3", "5", False, 0),
    ("5-3*2", "-1", False, 0),
    ("10/3", "3", False, 0),
    ("(4+5)*6", "54", False, 0),
    ("0-1+5", "4", False, 0),
    ("8/2*(2+2)", "16", False, 0),
    
    # Float mode tests
    ("3+2", "5.0000", True, 0),
    ("5/2", "2.5000", True, 0),

]

error_cases = [
    # Invalid characters
    ("2+a", "", False, 3),
    # Division by zero (integer)
    ("5/0", "", False, 1),
    # Division by zero (float)
    ("5/0", "", True, 2),
    # Mismatched parentheses
    ("(2+3", "", False, 4),
    ("2+3)", "", False, 4),
]

def run_calculator(input_str, float_mode=False):
    cmd = ["./build/app.exe"]
    if float_mode:
        cmd.append("--float")
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=input_str + "\n")
    return proc.returncode, stdout.strip(), stderr.strip()

@pytest.mark.parametrize("input_str,expected_output,use_float,exit_code", valid_cases)
def test_valid_expressions(input_str, expected_output, use_float, exit_code):
    return_code, output, error = run_calculator(input_str, use_float)
    assert return_code == exit_code
    assert error == ""
    assert output == expected_output

@pytest.mark.parametrize("input_str,expected_output,use_float,exit_code", error_cases)
def test_error_cases(input_str, expected_output, use_float, exit_code):
    return_code, output, error = run_calculator(input_str, use_float)
    assert return_code != 0
    assert output == ""

# Test whitespace handling
def test_whitespace_handling():
    return_code, output, error = run_calculator(" 2   +  (  3  * 4 )  ")
    assert return_code == 0
    assert output == "14"

# Test operator precedence
def test_operator_precedence():
    return_code, output, error = run_calculator("2+3*4")
    assert output == "14"
    return_code, output, error = run_calculator("(2+3)*4")
    assert output == "20"

# Test negative numbers
def test_negative_numbers():
    return_code, output, error = run_calculator("0-5-3")
    assert output == "-8"
    return_code, output, error = run_calculator("(0-2/10*3)", True)
    assert output == "-0.6000"

def test_unary_operators():
    return_code, output, error = run_calculator("-5-3")
    assert return_code != 0
    return_code, output, error = run_calculator("(/10*3)", True)
    assert return_code != 0
