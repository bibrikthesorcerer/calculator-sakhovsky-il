import re
import random
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QThread, Slot
from PySide6.QtWidgets import QApplication

from client.controller.networking import WebSocketClient, HTTPSender, HTTPSenderError
from client.model.manager import DatabaseManager

logger = logging.getLogger()


class AppFSM:
    class States:
        INPUT_WAIT = "input_wait"
        RESPONSE_WAIT = "response_wait"

    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(AppFSM, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self, window):
        self.window = window
        
        # magic parameters
        self.retry_max_attempts = 10
        self.retry_base_delay = 256
        self.retry_loop_cooldown = 5000
        self.is_server_reachable = True #иначе при первом запуске конфликтует с http реконектом

        # GUI tweaks
        self.window.retry_progress.setMaximum(self.retry_max_attempts)
        self.window.expression_input.returnPressed.connect(self.on_send_requested)
        self.window.send_button.clicked.connect(self.on_send_requested)
        
        # DB manager
        self.history_manager = DatabaseManager()
        self.history_manager.update_trigger.connect(self.window.refresh_local_data)
        self.db_thread = QThread()
        self.history_manager.moveToThread(self.db_thread)
        self.db_thread.started.connect(self.history_manager.setup_database)
        self.db_thread.finished.connect(self.history_manager.shutdown)
        self.db_thread.start()
        
        # networking
        self.http_sender = HTTPSender("0.0.0.0", 8000)
        self.ws_client = WebSocketClient("ws://0.0.0.0:8000/ws/sync", self.history_manager)
        self.sync_thread = QThread()
        self.ws_client.moveToThread(self.sync_thread)
        self.sync_thread.started.connect(self.ws_client.connect_to_server) # init WS connection
        self.sync_thread.finished.connect(self.ws_client.close)

        self.ws_client.connected.connect(self._on_connect)
        self.ws_client.disconnected.connect(self._on_disconnect)

        self.sync_thread.start()
        
        # init FSM state
        self.state = self.States.RESPONSE_WAIT
    
    @Slot()
    def _on_connect(self):
        self.transition_to_input_wait()
        self.window.connection_success.emit()
        
    @Slot()
    def _on_disconnect(self):
        self.transition_to_response_wait()        
        if(self.is_server_reachable):
            self.window.set_server_status("Connection failed.", "red") 

    def cleanup(self):
        logger.info("Got close signal, cleaning up")
        self.sync_thread.quit()
        self.sync_thread.wait()
        self.db_thread.quit()
        self.db_thread.wait()
        # overhead time for graceful close
        QTimer.singleShot(100, QApplication.quit)

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
                # update db and ui
                self._add_calculation_entry(body)
                self.window.show_feedback("Success", "lime")
            else:
                self.window.show_feedback(f"Error {status}", "red")
            # Use a cooldown timer before re-enabling input.
            QTimer.singleShot(self.window.cooldown, self.transition_to_input_wait)
        except (HTTPSenderError, ConnectionError) as e:
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
            self.is_server_reachable = True
            if success_callback:
                success_callback()
            else:
                self.transition_to_input_wait()
        except Exception as e:
            self.is_server_reachable = False
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

    def _add_calculation_entry(self, entry):
        """Puts an INSERT operation in a DB manager's Queue"""
        self.history_manager.enqueue_operation(
            'insert', 
            {
                'id': entry.get('id'),
                'expression': entry.get('expression'),
                'result': entry.get('result'),
                'timestamp': entry.get('timestamp')
            }
        )