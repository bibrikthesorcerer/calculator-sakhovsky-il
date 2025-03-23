import sys
import json
import logging
import http.client
from PySide6.QtWidgets import QApplication, QWidget, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox,
    QTextEdit, QLabel,
    QTableWidget, QTableWidgetItem,
    QHeaderView
)

class CalcApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.window = CalcWindow()
        self.window.show()

class CalcWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.http_sender = HTTPSender()

    def _init_ui(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Calculator App')

        self.policy = QSizePolicy()
        self.policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        
        # init main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

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
        self.expression_input = QTextEdit(self)
        self.expression_input.setFixedHeight(100)
        self.expression_input
        self.input_layout.addWidget(self.expression_input)
        
        # controls
        controls_layout = QHBoxLayout()
        self.input_layout.addLayout(controls_layout)
        
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self._send_evaluate_request)
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

    def _update_results_table(self, expression, result):
        self.result_table.insertRow(0)

        self.result_table.setItem(0, 0, QTableWidgetItem(expression))
        self.result_table.setItem(0, 1, QTableWidgetItem(result))

        self.result_table.scrollToTop()
    
    def _set_feedback(self, msg: str):
        self.feedback_label.setText(msg)
        self.feedback_label.setStyleSheet("color: red;")
    
    def _reset_feedback(self):
        self.feedback_label.setText("Enter an arithmetic expression")
        self.feedback_label.setStyleSheet("color: black;")

    def _send_evaluate_request(self):      
        # parse request
        expression = self.expression_input.toPlainText()
        float_mode = self.float_mode_checkbox.isChecked()
        try:
            status, body = self.http_sender.send_and_receive(
                HTTPSender.POST, 
                f"/calc?float={'true' if float_mode else 'false'}",
                expression,
                {"Content-Type": "application/json"}
            )
            if status == 200 and body is not None:
                self._update_results_table(expression, body)
                self._reset_feedback()
            else:
                self._set_feedback(f"Error {status}")
        except HTTPSenderError as e:
            self._set_feedback(f"Sender Error: {str(e)}")

    
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
            logging.error(f"Failed to initialize HTTP connection: {e}")
            raise HTTPSenderError(f"Failed to initialize connection: {e}")

    def _close_connection(self):
        """Close connection with server"""
        if hasattr(self, "_connection"):
            try:
                self._connection.close()
            except Exception as e:
                logging.warning(f"Failed to close HTTP connection: {e}")

    def check_connection(self):
        """Check if server is reachable"""
        self._init_connection()
        try:
            self._connection.connect()
        except Exception as e:
            logging.error(f"Connection check failed: {e}")
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
                logging.error(f"Failed to serialize data to JSON: {e}")
                raise HTTPSenderError(f"Data serialization error: {e}")

            try:
                self._connection.request(method, url, body, headers)
            except Exception as e:
                logging.error(f"HTTP request error: {e}")
                raise HTTPSenderError(f"HTTP request error: {e}")

            response = self._connection.getresponse()
            status = response.status
            raw_body = response.read()
            response.close()

            try:
                decoded_body = raw_body.decode("utf-8")
                parsed_body = json.loads(decoded_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logging.error(f"Failed to decode/parse response: {e}")
                raise HTTPSenderError(f"Response decoding/parsing error: {e}")

            return (status, parsed_body)
        finally:
            self._close_connection()


if __name__ == '__main__':
    app = CalcApp(sys.argv)
    sys.exit(app.exec_())