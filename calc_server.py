import os
import json
import logging
import argparse
import structlog
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
FLOAT_MODE = (FLOAT_FLAG, "FLOAT")
INT_MODE = (INT_FLAG, "INT")

def configure_logging():
    """Configures console and json output using structlog and logging"""
    # common processors for both outputs
    common_processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"), # timestamps
        structlog.processors.StackInfoRenderer(), # stack dumps
        structlog.processors.format_exc_info, # exception info
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # structlog config
    structlog.configure(
        processors=common_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # logger from logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # create Console log Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
    ))

    # create JSON log Handler
    file_handler = logging.FileHandler("calc_server.log")
    file_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    ))

    # add both handlers to standart logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)  

# init logging
configure_logging()
logger = structlog.get_logger()


class CalcManager:
    """
    Helper class which handles building and running calculator application

    Parameters
    ----------
        float_mode (bool): whether to run calc in FLOAT_MODE
        input_data (str): arithmetic expression passed for app to evaluate
    """
    def __init__(self, float_mode: bool, input_data: str):
        self.mode_flag, self.mode_str = FLOAT_MODE if float_mode else INT_MODE
        # convert str to bytes to pipe in stdin
        self.input_data = input_data.encode("utf-8")
        if not self._ensure_bin():
            raise Exception("Server cannot access or build app binary")
    
    def _ensure_bin(self) -> bool:
        # check if built binary exists
        if os.path.isfile('./build/app.exe'):
            logger.info("Binary found in filesystem")
            return True
        # try to build from make if make exists
        if os.path.isfile('./Makefile'):
            logger.info("Makefile found, attempting to build binary")
            run_res = subprocess.run(["make", APP_NAME])
            if run_res.returncode == 0:
                logger.info("Binary built successfully")
                return True
            else:
                logger.error("Failed to build binary")
                return False
        #  binary and Makefile are not present in fs
        logger.error("Binary and Makefile not found in filesystem")
        return False

    def run_app(self) -> tuple[int, str]:
        logger.info("Running calculator application", mode=self.mode_str)
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
        logger.info("Calculator application finished with exit code 0", output=output)
        return self.result


class CalculatorRequestHandler(BaseHTTPRequestHandler):
    """
    Custom handler for web requests used by HTTPServer.  
    Handles Calculator-related requests
    """
    def _url_dispatcher(self, path: str) -> object:
        router = {
            "/calc" : self._calc_post_response,
            "/health": self._healthcheck_handler
        }
        route_handler = router.get(path, self._404_handler)
        return route_handler
    
    def _404_handler(self) -> tuple[int, bytes]:
        return (HTTPStatus.NOT_FOUND, self._make_error_body("Not Found"))
    
    def _405_handler(self) -> tuple[int, bytes]:
        return (HTTPStatus.METHOD_NOT_ALLOWED, self._make_error_body("Method Not Allowed"))
    
    def _healthcheck_handler(self) -> tuple[int, bytes]:
        if self.command != "GET":
            return self._405_handler()
        return (HTTPStatus.OK, json.dumps("OK").encode("utf-8"))

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
    
    def log_request(self, code = "-", size = "-") -> None:
        logger.info(f"{self.command} request handled", path=self.url.path, client=self.client_address)

    def _make_error_body(self, msg: str, **kwargs) -> bytes:
        response_body = json.dumps({
                "error": msg,
                **kwargs
            })
        logger.error("An error occured", path=self.url.path, error=msg, **kwargs)
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
        float_mode = False if float_mode == "false" else True
        
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
        if self.command != "POST":
            return self._405_handler()
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
                        e.args[0], # CalcManager exceptions contain only error message
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
        logger.info(f"Incoming POST request", path=self.url.path, client=self.client_address)
        route_handler = self._url_dispatcher(self.url.path)
        resp_code, resp_body = route_handler()
        self._send_json_response(resp_code, resp_body)

    def do_GET(self):
        logger.info(f"Incoming GET request", path=self.url.path, client=self.client_address)
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
        logger.info("Starting server", address=address, port=port)
        server = HTTPServer((address, port), CalculatorRequestHandler)
    except Exception as e:
        logger.error("Server initialization error!", error=str(e))
        exit(1)
    
    # run server
    try:
        logger.info("Server is up on", address=address, port=port)
        server.serve_forever()
    except KeyboardInterrupt:
       logger.info("Server recieved shutdown signal")
    except Exception as e:
        logger.error("Server error!", error=str(e))
    finally:
        server.server_close()
        logger.info("Server closed")

if __name__ == "__main__":
    args = parse_args()
    address = args.address
    port = args.port
    run_calc_server(address, port)
