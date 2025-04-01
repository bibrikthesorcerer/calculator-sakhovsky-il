import logging
import sqlite3
from queue import Queue, Empty
from PySide6.QtCore import QMutex, QMutexLocker, QObject, Signal, Slot

logger = logging.getLogger()


class DatabaseManager(QObject):
    """SQLite3 manager class. Runs in separate thread and uses Queue and Mutex to ensure thread-safe operations"""
    update_trigger = Signal(list)  # signal to notify model of changes
    operation_available = Signal() # signal for queue operations

    def __init__(self):
        super().__init__()
        self.operation_queue = Queue()
        self.running = True
        self.mutex = QMutex()
        self.operation_available.connect(self.process_queue)
    
    def setup_database(self):
        """Connect to db and create history table if not present"""
        self.conn = sqlite3.connect('./client/local_history.sqlite3')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                expression TEXT,
                result TEXT,
                timestamp DATETIME
            )''')
        self.conn.commit()
        # initial UI
        self._emit_all_data()

    def process_queue(self):
        """Listen to Queue and perform requested operations"""
        while True and self.running:
            # pop data from queue
            with QMutexLocker(self.mutex):
                try:
                    op_type, data = self.operation_queue.get(timeout=0.1)
                except Empty:
                    logger.debug("DB: Empty Queue, all operations proccessed")
                    break

            # process data from queue
            try:
                if op_type == 'insert':
                    self._local_insert(data)
                elif op_type == 'sync':
                    self._sync_data(data)
                logger.debug(f"DB: Executed {op_type}")
            except Exception as e:
                logger.error(f"DB: Operation failed: {e}")

    @Slot(str, dict)
    def enqueue_operation(self, op_type, data):
        with QMutexLocker(self.mutex):
            self.operation_queue.put((op_type, data))
            self.operation_available.emit()

    def _local_insert(self, data):
        """Insert new calculation result"""
        self.conn.execute('''
            INSERT INTO history (id, expression, result, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (data['id'], data['expression'], data['result'], data['timestamp']))
        self.conn.commit()
        self._emit_all_data()
    
    def _sync_data(self, server_data):
        """Sync server data with local database"""
        cursor = self.conn.cursor()

        server_ids = []
        server_timestamps = []
        
        for record in server_data:
            server_ids.append(record['id'])
            server_timestamps.append(record['timestamp'])
            cursor.execute('''
                INSERT INTO history (id, expression, result, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    expression = excluded.expression,
                    result = excluded.result,
                    timestamp = excluded.timestamp
            ''', (record['id'], record['expression'], record['result'], record['timestamp']))
        
        if server_data:
            max_server_ts = max(server_timestamps)
            placeholders = ','.join(['?'] * len(server_ids)) # ?,?,?,?,
            
            cursor.execute(f'''
                DELETE FROM history
                WHERE id NOT IN ({placeholders})
                AND timestamp <= ?
            ''', (*server_ids, max_server_ts))

        self.conn.commit()
        self._emit_all_data()
    
    def _emit_all_data(self):
        """Uses signal mechanism to emit current db state"""
        cursor = self.conn.execute('''
            SELECT id, expression, result, timestamp
            FROM history 
            ORDER BY timestamp DESC
        ''')
        data = [
            {'id': row[0], 'expression': row[1], 'result': row[2], 'timestamp': row[3]} 
            for row in cursor
        ]
        self.update_trigger.emit(data)

    def shutdown(self):
        logger.info("DB: Shutting down...")
        self.running = False
        self.conn.close()