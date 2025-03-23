import re
import sys
import json
import random
import logging
import http.client
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRegularExpression, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox,
    QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()


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
            logger.error(f"Failed to initialize HTTP connection: {e}")
            raise HTTPSenderError(f"Failed to initialize connection: {e}")

    def _close_connection(self):
        """Close connection with server"""
        if hasattr(self, "_connection"):
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"Failed to close HTTP connection: {e}")

    def check_connection(self):
        """Check if server is reachable"""
        self._init_connection()
        try:
            self._connection.connect()
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
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
                logger.error(f"Failed to serialize data to JSON: {e}")
                raise HTTPSenderError(f"Data serialization error: {e}")

            try:
                self._connection.request(method, url, body, headers)
            except Exception as e:
                logger.error(f"HTTP request error: {e}")
                raise HTTPSenderError(f"HTTP request error: {e}")

            response = self._connection.getresponse()
            status = response.status
            raw_body = response.read()
            response.close()

            try:
                decoded_body = raw_body.decode("utf-8")
                parsed_body = json.loads(decoded_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.error(f"Failed to decode/parse response: {e}")
                raise HTTPSenderError(f"Response decoding/parsing error: {e}")

            return (status, parsed_body)
        finally:
            self._close_connection()


class CalcApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.window = CalcWindow()
        self.window.show()
        # init fsm and start initial connection check
        self.window.fsm.transition_to_response_wait()
        QTimer.singleShot(0, self.window.fsm.check_server_connection)


class CalcWindow(QWidget):
    connection_success = Signal()
    connection_failure = Signal(str)

    def __init__(self):
        super().__init__()
        self.cooldown = 2000
        self.max_input_size = 1024
        self.expression_regex = QRegularExpression(r"[^0-9+\-*/\s()]")
        self.connection_success.connect(self._connection_success_handler)
        self.connection_failure.connect(self._connection_failure_handler)
        self.fsm = AppFSM(self)
        self._init_ui()

    def _init_ui(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Calculator App')

        self.policy = QSizePolicy()
        self.policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        
        # init main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # init server panel
        self.server_widget = QWidget()
        self._init_server_info()
        self.main_layout.addWidget(self.server_widget)

        # header label
        header_label = QLabel("<h1>Expression Form</h1>")
        self.main_layout.addWidget(header_label)

        # user feedback label
        self.feedback_label = QLabel("Enter an arithmetic expression", self)
        self.feedback_label.setStyleSheet("color: black;")
        self.main_layout.addWidget(self.feedback_label)
        
        # add input widget
        self.input_widget = QWidget()
        self._init_input_fields()
        self.main_layout.addWidget(self.input_widget)

        # results label
        result_label = QLabel("Calculated Results")
        self.main_layout.addWidget(result_label)

        # add results
        self.results_widget = QWidget()
        self._init_results_table()
        self.main_layout.addWidget(self.results_widget)

        self.show()

    def _init_input_fields(self):
        self.input_layout = QVBoxLayout(self.input_widget)
        self.input_layout.setAlignment(Qt.AlignTop)
        
        # expression input
        self.expression_input = QLineEdit(self)
        self.expression_input.returnPressed.connect(self.fsm.on_send_requested)
        self.input_layout.addWidget(self.expression_input)
        
        # controls
        controls_layout = QHBoxLayout()
        self.input_layout.addLayout(controls_layout)
        
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.fsm.on_send_requested)
        controls_layout.addWidget(self.send_button)

        self.float_mode_checkbox = QCheckBox("Float Mode", self)
        controls_layout.addWidget(self.float_mode_checkbox)

    def _init_results_table(self):
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create the results table
        self.result_table = QTableWidget(0, 2)
        self.result_table.setHorizontalHeaderLabels(["Expression", "Result"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.results_layout.addWidget(self.result_table)

    def _init_server_info(self):
        self.server_layout = QHBoxLayout(self.server_widget)

        self.server_status = QLabel("Server state unknown")
        self.server_status.setStyleSheet("color: black;")
        self.server_layout.addWidget(self.server_status)

        self.retry_progress = QProgressBar()
        self.retry_progress.setMaximum(self.fsm.retry_max_attempts)
        self.retry_progress.setVisible(False)
        self.server_layout.addWidget(self.retry_progress)

    def set_server_status(self, text:str, text_color:str):
        self.server_status.setText(text)
        self.server_status.setStyleSheet(f"color: {text_color};")

    def init_retry_progress_bar(self):
        self.retry_progress.setValue(0)
        self.retry_progress.setVisible(True)

    def increase_retry_progress_bar(self):
        self.retry_progress.setValue(self.retry_progress.value()+1)

    def hide_retry_progress_bar(self):
        self.retry_progress.setVisible(False)

    def _get_timestamp(self) -> str:
        return datetime.now().strftime(" %H:%M:%S %d %b %Y")

    def update_results_table(self, expression, result):
        self.result_table.insertRow(0)

        self.result_table.setItem(0, 0, QTableWidgetItem(expression))
        self.result_table.setItem(0, 1, QTableWidgetItem(result))

        self.result_table.scrollToTop()
    
    def show_feedback(self, msg: str, text_color:str):
        self.feedback_label.setText(msg)
        self.feedback_label.setStyleSheet(f"color: {text_color}")
    
    def reset_feedback(self):
        self.feedback_label.setText("Enter an arithmetic expression")
        self.feedback_label.setStyleSheet("color: black;")

    def disable_inputs(self):
        self.send_button.setEnabled(False)
        self.expression_input.setEnabled(False)
        self.float_mode_checkbox.setEnabled(False)
        logger.info("CalcWindow: Inputs have been disabled.")
    
    def enable_inputs(self):
        self.send_button.setEnabled(True)
        self.expression_input.setEnabled(True)
        self.float_mode_checkbox.setEnabled(True)
        self.reset_feedback()
        logger.info("CalcWindow: Inputs have been enabled.")

    def _connection_success_handler(self):
        self.set_server_status(f"Connected [{self._get_timestamp()}]", "lime")
        self.hide_retry_progress_bar()

    def _connection_failure_handler(self, error_msg: str):
        self.set_server_status(f"{error_msg} [{self._get_timestamp()}]", "red")
        self.hide_retry_progress_bar()

    def validate_expression(self, expression) -> bool:
        # validate the expression
        if len(expression) > self.max_input_size \
            or self.expression_regex.match(expression).hasMatch():
            self.show_feedback("Invalid arithmetic expression", "red")
            return False
        return True


class AppFSM:
    class States:
        INPUT_WAIT = "input_wait"
        RESPONSE_WAIT = "response_wait"

    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(AppFSM, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self, window:CalcWindow):
        # magic parameters
        self.retry_max_attempts = 10
        self.retry_base_delay = 256
        self.retry_loop_cooldown = 5000
        self.http_sender = HTTPSender()
        self.window = window
        self.state = self.States.RESPONSE_WAIT

    def transition_to_input_wait(self):
        logger.info("FSM: Transitioning to INPUT_WAIT")
        self.state = self.States.INPUT_WAIT
        if self.window:
            self.window.enable_inputs()
    
    def transition_to_response_wait(self):
        logger.info("FSM: Transitioning to RESPONSE_WAIT")
        self.state = self.States.RESPONSE_WAIT
        if self.window:
            self.window.disable_inputs()

    def on_send_requested(self):
        """Called by CalcWindow when user clicks Send"""
        if self.state != self.States.INPUT_WAIT:
            logger.error("FSM: Not ready to send. Waiting for previous response.")
            return
        else:
            self._send_request()

    def _send_request(self):
        expression = self.window.expression_input.text()
        expression = re.sub(r"\s", "", expression)
        # validate expression
        if not self.window.validate_expression(expression):
            self.window.show_feedback("Invalid arithmetic expression", "red")
            return
        
        # transition to response wait state
        self.transition_to_response_wait()
        # show feedback that processing is underway
        self.window.show_feedback("Sending request...", "black")
        
        float_mode = self.window.float_mode_checkbox.isChecked()
        float_param = "true" if float_mode else "false"
        try:
            status, body = self.http_sender.send_and_receive(
                HTTPSender.POST,
                f"/calc?float={float_param}",
                expression,
                {"Content-Type": "application/json"}
            )
            if status == 200 and body is not None:
                # update ui
                self.window.update_results_table(expression, body)
                self.window.show_feedback("Success", "lime")
            else:
                self.window.show_feedback(f"Error {status}", "red")
            # Use a cooldown timer before re-enabling input.
            QTimer.singleShot(self.window.cooldown, self.transition_to_input_wait)
        except HTTPSenderError as e:
            self.check_server_connection(success_callback=self._send_request)
        
    def check_server_connection(self, success_callback=None):
        if self.state != self.States.RESPONSE_WAIT:
            logger.error("FSM: Cannot send request. Waiting for user input.")
            return
        try:
            self.http_sender.check_connection()
            self.window.connection_success.emit()
            if success_callback:
                success_callback()
            else:
                self.transition_to_input_wait()
        except HTTPSenderError as e:
            self.window.init_retry_progress_bar()
            # enter retry loop
            self._retry_connect_to_server(0, success_callback)
    
    def _retry_connect_to_server(self, attempts, success_callback=None):
        if self.state != self.States.RESPONSE_WAIT:
            logger.error("FSM: Cannot send request. Waiting for user input.")
            return
        try: 
            self.http_sender.check_connection()
            # exit retry loop
            self.window.connection_success.emit()
            if success_callback:
                success_callback()
            else:
                self.transition_to_input_wait()
        except Exception as e:
            attempts += 1
            if attempts > self.retry_max_attempts:
                self.window.connection_failure.emit(
                    f"Unable to reach server. Retry in 5sec."
                )
                QTimer.singleShot(self.retry_loop_cooldown, lambda: self.check_server_connection(success_callback))
                return
            # update gui
            self.window.set_server_status(f"Connection attempt #{attempts}", "orange")
            self.window.increase_retry_progress_bar()
            # retry with jitter
            exp_delay = self.retry_base_delay * (2^attempts+1)
            exp_delay = min(self.window.cooldown, exp_delay)
            jitter = random.randint(100, 1000)
            delay = exp_delay+jitter
            logger.info(f"Retry #{attempts} delay:{delay}, base:{self.retry_base_delay}, exp:{exp_delay}, jitter:{jitter}")
            QTimer.singleShot(delay, lambda: self._retry_connect_to_server(attempts, success_callback))


if __name__ == '__main__':
    app = CalcApp(sys.argv)
    sys.exit(app.exec_())