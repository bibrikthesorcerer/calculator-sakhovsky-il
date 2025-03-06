import json
import argparse
from typing import Any
from http.server import HTTPServer
from functools import cached_property
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse, ParseResult


class CalculatorRequestHandler(BaseHTTPRequestHandler):
    """
    Custom handler for web requests used by HTTPServer.  
    Handles Calculator-related requests
    """
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
    
    def _send_json_response(self, resp_code, resp_body):
        # add response code and headers to header buffer
        self.send_response(resp_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        # write response to output stream
        self.wfile.write(resp_body)

    def do_POST(self):
        resp_dict = dict()
        if self.url.path:
            resp_dict["path"] = self.url.path
        if self.query_data:
            resp_dict["query"] = self.query_data
        if self.post_data:
            resp_dict["requestBody"] = self.post_data.decode("utf-8")
        
        resp_body = json.dumps(resp_dict)
        self._send_json_response(200, resp_body.encode("utf-8"))


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
