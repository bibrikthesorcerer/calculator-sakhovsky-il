import logging
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRegularExpression, QTimer, Signal, QAbstractTableModel
from PySide6.QtWidgets import (
    QApplication, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox,
    QLineEdit, QLabel,
    QTableView, QHeaderView,
    QProgressBar, QTableView
)

from client.controller.controller import AppFSM


logger = logging.getLogger()


class SyncTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = ["ID", "Expression", "Result", "Timestamp"]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            return [
                self._data[row]['id'],
                self._data[row]['expression'],
                self._data[row]['result'],
                self._data[row]['timestamp']
            ][col]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]

    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class CalcApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.window = CalcWindow()
        self.window.show()
        # init fsm and start initial connection check
        self.window.fsm.transition_to_response_wait()
        QTimer.singleShot(0, self.window.fsm.check_server_connection)
        self.aboutToQuit.connect(self.window.fsm.cleanup)


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
        self.result_table = QTableView()
        self.model = SyncTableModel()
        self.result_table.setModel(self.model)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

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

    def refresh_local_data(self, data):
        self.model.update_data(data)
    
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

