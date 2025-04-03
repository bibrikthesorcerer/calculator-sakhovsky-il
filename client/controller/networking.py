import json
import logging
import http.client
from PySide6.QtCore import QTimer, Signal, Slot, QUrl, QObject
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtNetwork import QAbstractSocket

logger = logging.getLogger()


class WebSocketClient(QObject):
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, url, db_manager):
        super().__init__()
        self.is_active = False
        self.reconnect_interval = 5000 # ms   
        self.db_manager = db_manager
        self.url = QUrl(url)   
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.connect_to_server)    

    def _connect_signals(self):        
        self.ws.connected.connect(self._on_connected)
        self.ws.disconnected.connect(self._on_disconnected)
        self.ws.textMessageReceived.connect(self._on_message_received)
        self.ws.errorOccurred.connect(self._on_error)

    def connect_to_server(self):
        """Initiate WebSocket connection"""
        self.ws = QWebSocket(parent=self)  
        self._connect_signals()
        self.is_active = True
        self.ws.open(self.url)
    

    def close(self):
        """Graceful shutdown"""
        logger.info("WS: Shutting down...")
        self.is_active = False
        self.reconnect_timer.stop()
        if self.ws.state() == QAbstractSocket.ConnectedState:
            self.ws.close()

    def reconnect(self):
        if self.is_active:  # only reconnect if app is still active
            logger.debug(f"WS: Reconnecting in {self.reconnect_interval}ms")
            self.reconnect_timer.start(self.reconnect_interval)
        else:
            logger.debug("WS: Disconnected during shutdown")

    @Slot()
    def _on_connected(self):
        """Handle successful connection"""
        self.connected.emit()
        logger.info("WS: WebSocket connected")
        if self.reconnect_timer.isActive():
            logger.debug("WS: Connected after retries. Stopping reconnect timer")
            self.reconnect_timer.stop()

    @Slot()
    def _on_disconnected(self):
        """Handle connection loss"""
        self.disconnected.emit()
        self.reconnect()

    @Slot(str)
    def _on_message_received(self, message):
        """Process incoming messages"""
        logger.debug("WS: Received message")
        try:
            data = json.loads(message)
            if isinstance(data, list):
                self.db_manager.enqueue_operation('sync', data)
        except json.JSONDecodeError as e:
            self.error_occurred.emit(f"Invalid JSON: {str(e)}")

    @Slot(str)
    def _on_error(self, error):
        """Handle WebSocket errors"""
        error_msg = self.ws.errorString()
        logging.error(f"WS: Error occured: {error_msg}")
        self.error_occurred.emit(f"WebSocket error: {error_msg}")
        self.reconnect()


class HTTPSenderError(Exception):
    """Custom exception class for HTTPSender errors."""
    pass


class HTTPSender:
    """A wrapper HTTP client class which handles communication with the server."""
    GET = "GET"
    POST = "POST"
    
    def __init__(self, addr="0.0.0.0", port=8000):
        self.addr = addr
        self.port = port

    def _init_connection(self):
        """Initialize connection parameters"""
        try:
            self._connection = http.client.HTTPConnection(self.addr, self.port, timeout=10)
        except Exception as e:
            logger.error(f"HTTP: Failed to initialize HTTP connection: {e}")
            raise HTTPSenderError(f"Failed to initialize connection: {e}")

    def _close_connection(self):
        """Close connection with server"""
        if hasattr(self, "_connection"):
            try:
                self._connection.close()
            except Exception as e:
                logger.error(f"HTTP: Failed to close HTTP connection: {e}")

    def check_connection(self):
        """Check if server is reachable"""
        self._init_connection()
        try:
            self._connection.request(HTTPSender.GET, "/health")
            response = self._connection.getresponse()
            status = response.status
            response.close()
            if status == 200:
                logger.info("HTTP: Healthcheck OK")
            else:
                raise HTTPSenderError(f"Got response {status} but not 200")
        except Exception as e:
            logger.error(f"HTTP: Connection check failed: {e}")
            raise HTTPSenderError(f"Connection check failed: {e}")
        finally:
            self._close_connection()

    def send_and_receive(self, method: str, url: str, data, headers: dict = {}) -> tuple[int, str|dict]:
        """
        Send an HTTP request and get the response.

        :param method: HTTP method (e.g., GET, POST)
        :param url: URL for the HTTP request
        :param data: Data to be sent (will be serialized to JSON)
        :param headers: HTTP Headers to include in the request
        :return: A tuple (status, parsed_json_body)
        :raises HTTPSenderError: If any error occurs during the request/response cycle
        """
        self._init_connection()
        try:
            try:
                # conver body data to json
                body = json.dumps(data)
            except (TypeError, ValueError) as e:
                logger.error(f"HTTP: Failed to serialize data to JSON: {e}")
                raise HTTPSenderError(f"Data serialization error: {e}")

            try:
                self._connection.request(method, url, body, headers)
            except Exception as e:
                logger.error(f"HTTP: HTTP request error: {e}")
                raise HTTPSenderError(f"HTTP request error: {e}")

            response = self._connection.getresponse()            
            status = response.status
            raw_body = response.read()
            response.close()
            if (status != 200):
                return(status,None)
            try:
                decoded_body = raw_body.decode("utf-8")
                parsed_body = json.loads(decoded_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.error(f"HTTP: Failed to decode/parse response: {e}")
                raise HTTPSenderError(f"Response decoding/parsing error: {e}")
            logger.info("HTTP: Handled response from server")
            return (status, parsed_body)
        finally:
            self._close_connection()

