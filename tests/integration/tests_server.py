import subprocess
import pytest
import signal
import os

begin_curl_request = 'curl -X POST "http://0.0.0.0:8000/calc?float='
end_curl_request = '" -H "Content-Type: application/json" -d'

@pytest.fixture(autouse=True, scope="session")
def run_around_tests():
    process = subprocess.Popen(
        "python3 -m calc_server",
        shell = True,
        preexec_fn = os.setsid
    )
    while True:
        check = subprocess.run(
            begin_curl_request + 'false' + end_curl_request + ' \'\"1 + 3-2\"\'',
            shell = True,
            text = True,
            capture_output = True
        )
        if check.returncode != 7:
            break
    yield
    os.killpg(os.getpgid(process.pid), signal.SIGTERM) 

correct_curl_requests = [
    (begin_curl_request + 'false' + end_curl_request + ' \'\"1 + 3-2\"\'', '"2"'),
    (begin_curl_request + 'true'  + end_curl_request + ' \'\"2 / 4 - 1\"\'', '"-0.5000"'),
    
    (begin_curl_request + 'false' + end_curl_request + ' \'\"4 * 7 - 6 * 3\"\'', '"10"'),
    (begin_curl_request + 'true'  + end_curl_request + ' \'\"32 * 7 / 63 + 41\"\'', '"44.5556"'),
    
    (begin_curl_request + 'false' + end_curl_request + ' \'\"(4+10) / 3 + (2 * 5 - 1)\"\'', '"13"'),
    (begin_curl_request + 'true'  + end_curl_request + ' \'\"(8 * 9 - 67) / (5 - 7 * 6) + 23\"\'', '"22.8649"'),

    ('curl -X POST "http://0.0.0.0:8000/calc' + end_curl_request + ' \'\"7 - 4 +3*(5 + 9*8 - (7+3) / 10) * 2\"\'', '"459"')
]

erroneous_curl_requests = [
    # Incorrect input of numbers/operations
    (begin_curl_request + 'false' + end_curl_request + ' \'\"2 * 7 8\"\'', "error"),
    (begin_curl_request + 'true'  + end_curl_request + ' \'\"48 * 9 +7^2\"\'', "error"),

    # Incorrect input of parentheses
    (begin_curl_request + 'false' + end_curl_request + ' \'\"( 3 - 8 * (3 + 1)))\"\'', "error"),
    (begin_curl_request + 'true'  + end_curl_request + ' \'\"(37 * 9)) + 3 - 245\"\'', "error"),
    
    # Division by "zero"
    (begin_curl_request + 'false' + end_curl_request + ' \'\"128 - (37 + 90) / (15 - 5 * 3)\"\'', "error"),
    (begin_curl_request + 'true'  + end_curl_request + ' \'\"275 + 1 / (78 / (1000 * 7 * (91 + 111)) )- 28\"\'', "error"),

    # Incorrect POST request
    ('curl -X POST "http://0.0.0.0:8000/calc?float=fool' + end_curl_request + ' \'\"1 + 3-2\"\'', "error"),
    ('curl -X POST "http://0.0.0.0:8000/app?float=true'  + end_curl_request + ' \'\"1 + 3-2\"\'', "error"),
    (begin_curl_request + 'false" -H "Content-Type: text/html" -d \'\"1 + 3-2\"\'', "error"),
    (begin_curl_request + 'false' + end_curl_request + '\"1 + 3-2\"', "")
]

@pytest.mark.parametrize("curl_request, expected_output", correct_curl_requests)
def test_correct_input(curl_request, expected_output):
    result = subprocess.run(
        curl_request,
        shell = True,
        text = True,
        capture_output = True
    )
    assert result.stdout == expected_output

@pytest.mark.parametrize("curl_request, expected_output", erroneous_curl_requests)
def test_erroneous_input(curl_request, expected_output):
    result = subprocess.run(
        curl_request,
        shell = True,
        text = True,
        capture_output = True
    )
    if result.stdout == '':
        assert result.returncode != 0
    else:
        assert expected_output in result.stdout
