import argparse
from http.server import HTTPServer
from functools import cached_property
from http.server import BaseHTTPRequestHandler

class CalculatorRequestHandler(BaseHTTPRequestHandler):
    """
    Custom handler for web requests used by HTTPServer.  
    Handles Calculator-related requests
    """
    pass


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
