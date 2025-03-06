import os
import json
import argparse
import subprocess
from typing import Any
from http import HTTPStatus
from http.server import HTTPServer
from functools import cached_property
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse, ParseResult

APP_NAME = "./build/app.exe"
FLOAT_FLAG = "--float"
INT_FLAG = ""


class CalcManager:
    """
    Helper class which handles building and running calculator application

    Parameters
    ----------
        float_mode (bool): whether to run calc in FLOAT_MODE
        input_data (str): arithmetic expression passed for app to evaluate
    """
    def __init__(self, float_mode: bool, input_data: str):
        self.mode_flag = FLOAT_FLAG if float_mode else INT_FLAG
        # convert str to bytes to pipe in stdin
        self.input_data = input_data.encode("utf-8")

    def run_app(self) -> tuple[int, str]:
        app_process = subprocess.Popen(
            [APP_NAME, self.mode_flag],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = app_process.communicate(input=self.input_data)
        # process returns data in bytes - decode 'em and strip \n
        output = stdout.decode("utf-8").strip()
        if app_process.returncode != 0:
            raise Exception(f"Calculator application exited with code {app_process.returncode}")
        self.result = output
        return self.result


class CalculatorRequestHandler(BaseHTTPRequestHandler):
    """
    Custom handler for web requests used by HTTPServer.  
    Handles Calculator-related requests
    """
    def _url_dispatcher(self, path: str) -> object:
        router = {
            "/calc" : self._calc_post_response,
        }
        route_handler = router.get(path, self._404_handler)
        return route_handler
    
    def _404_handler(self) -> tuple[int, bytes]:
        return (404, self._make_error_body("Not Found"))

    @cached_property
    def url(self) -> ParseResult:
        return urlparse(self.path)
 
    @cached_property
    def query_data(self) -> dict[str, Any]:
        return dict(parse_qsl(self.url.query))

    @cached_property
    def post_data(self) -> bytes:
        content_length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(content_length)
    
    def _make_error_body(self, msg: str, **kwargs) -> bytes:
        response_body = json.dumps({
                "error": msg,
                **kwargs
            })
        return response_body.encode("utf-8")
    
    def _validate_request(self) -> bool | tuple[bool, str]:
        # content-type validation
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('application/json'):
            raise Exception(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE.value,
                self._make_error_body("Invalid Content-Type - must be application/json")
            )
        
        # float-mode validation
        float_mode = self.query_data.get("float", "false")
        if float_mode not in ["false", "true"]:
            raise Exception(
                HTTPStatus.BAD_REQUEST.value,
                self._make_error_body("Incorrect float value")
            )
        
        # requestBody data validation
        if not self.post_data:
            raise Exception(
                HTTPStatus.BAD_REQUEST.value,
                self._make_error_body("Empty requestBody")
            )
        
        input_data = json.loads(self.post_data)
        if not isinstance(input_data, str):
            raise Exception(
                HTTPStatus.BAD_REQUEST.value,
                self._make_error_body("Incorrect input data", input=input_data)
            )
        
        return (float_mode, input_data)

    def _calc_post_response(self) -> tuple[int, bytes]:
        # validate input
        try:
            float_mode, input_data = self._validate_request()
        except Exception as e:
            return e.args
        
        # create CalcManager and ensure binary is present in fs
        try:
            app = CalcManager(float_mode, input_data)
            # run app and get output from piped stdout
            output = app.run_app()
        except Exception as e:
            return (HTTPStatus.INTERNAL_SERVER_ERROR.value, 
                    self._make_error_body(
                        e.args,
                        input=self.post_data.decode("utf-8"),
                    ))
        
        response_body = json.dumps(output)
        return (HTTPStatus.OK.value, response_body.encode("utf-8"))
        
    def _send_json_response(self, resp_code: int, resp_body: bytes):
        # add response code and headers to header buffer
        self.send_response(resp_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        # write response to output stream
        self.wfile.write(resp_body)

    def do_POST(self):
        route_handler = self._url_dispatcher(self.url.path)
        resp_code, resp_body = route_handler()
        self._send_json_response(resp_code, resp_body)


def parse_args() -> argparse.Namespace:
    """Returns parsed Namespace of module arguments"""
    parser = argparse.ArgumentParser()
    # positional args
    parser.add_argument("address", nargs="?", help="Server Address", type=str, default="0.0.0.0")
    parser.add_argument("port", nargs="?", help="Server Port", type=int, default=8000)
    # flag-based args
    parser.add_argument("-a", "--Address", dest="address", help="Server Address (overrides positional argument)", type=str)
    parser.add_argument("-p", "--Port", dest="port", help="Server Port (overrides positional argument)", type=int)
    return parser.parse_args()

def run_calc_server(address: str, port: int):
    # init server
    try:
        server = HTTPServer((address, port), CalculatorRequestHandler)
    except Exception as e:
        print(f"Server initialization Error! {str(e)}")
        exit(1)
    
    # run server
    try:
        print(f"Server is up on {address}:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Received shutdown signal")
    finally:
        server.server_close()
        print("Server is down!")


if __name__ == "__main__":
    args = parse_args()
    address = args.address
    port = args.port
    run_calc_server(address, port)
