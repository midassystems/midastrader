import os
import logging
import threading
import time
from queue import PriorityQueue


class SystemLogger:
    """
    A singleton logger class for logging messages to a file, terminal, or both.

    This class initializes a logger instance that can output logs to a file, terminal, or both,
    based on the specified configuration. It ensures that only one logger instance exists throughout
    the application.

    Args:
        name (str, optional): Name of the logger. Defaults to "system".
        output_format (str, optional): Output format. Can be "file", "terminal", or "both". Defaults to "file".
        output_file_path (str, optional): Directory path to store the log file. Defaults to "output/".
        level (int, optional): Logging level (e.g., logging.INFO). Defaults to logging.INFO.

    Methods:
        get_logger(): Returns the singleton logger instance.
    """

    _instance = None

    def __new__(
        cls,
        name="system",
        output_format="file",
        output_file_path="output/",
        level=logging.INFO,
        flush_interval=1.0,
        buffer_size=100,
    ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(
                name,
                output_format,
                output_file_path,
                level,
                flush_interval,
                buffer_size,
            )
        return cls._instance

    def _initialize(
        self,
        name,
        output_format,
        output_file_path,
        level,
        flush_interval,
        buffer_size,
    ):
        """
        Initialize the logger with file and/or terminal output.

        Args:
            name (str): Name of the logger.
            output_format (str): Output format ("file", "terminal", or "both").
            output_file_path (str): Path to store log files.
            level (int): Logging level.
        """
        self.logger = logging.getLogger(f"{name}_logger")
        self.logger.setLevel(level)
        self.flush_interval = flush_interval
        self.buffer_size = buffer_size
        self.buffer = PriorityQueue()  # Thread-safe priority queue
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        if output_format in ["file", "both"]:
            if not os.path.exists(output_file_path):
                os.makedirs(output_file_path, exist_ok=True)
            log_file_name = os.path.join(output_file_path, f"{name}.log")
            file_handler = logging.FileHandler(log_file_name, mode="w")
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(file_handler)
        if output_format in ["terminal", "both"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(stream_handler)

        # Start background flusher thread
        self.flusher_thread = threading.Thread(
            target=self._flush_daemon,
            daemon=True,
        )
        self.flusher_thread.start()

    def log(self, level, message):
        """
        Add a log message to the buffer with a timestamp.

        Args:
            level (int): Logging level (e.g., logging.INFO).
            message (str): The log message.
        """
        timestamp = time.time()
        with self.lock:
            self.buffer.put((timestamp, level, message))
            if self.buffer.qsize() >= self.buffer_size:
                self._flush()

    def info(self, message):
        self.log(logging.INFO, message)

    def debug(self, message):
        self.log(logging.DEBUG, message)

    def warning(self, message):
        self.log(logging.WARNING, message)

    def error(self, message):
        self.log(logging.ERROR, message)

    def critical(self, message):
        self.log(logging.CRITICAL, message)

    def _flush_daemon(self):
        """
        Background thread that periodically flushes the buffer.
        """
        while not self.stop_event.is_set():
            time.sleep(self.flush_interval)
            self._flush()

    def _flush(self):
        """
        Flush the buffer to the logger.
        """
        with self.lock:
            while not self.buffer.empty():
                timestamp, level, message = self.buffer.get()
                self.logger.log(level, message)

    def stop(self):
        """
        Stop the background flusher thread and flush any remaining logs.
        """
        self.stop_event.set()
        self.flusher_thread.join()
        self._flush()

    @classmethod
    def get_logger(cls):
        """
        Retrieve the singleton logger instance.

        Returns:
            logging.Logger: The initialized logger instance.

        Raises:
            RuntimeError: If the logger has not been initialized.
        """
        if cls._instance is None:
            raise RuntimeError(
                "SystemLogger is not initialized. Call the constructor first."
            )
        return cls._instance.logger
