from http.server import HTTPServer
from functools import cached_property
from http.server import BaseHTTPRequestHandler

class CalculatorRequestHandler(BaseHTTPRequestHandler):
    """
    Custom handler for web requests used by HTTPServer.  
    Handles Calculator-related requests
    """
    pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), CalculatorRequestHandler)
    try:
        print("Server is up!")
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("Server is down!")
