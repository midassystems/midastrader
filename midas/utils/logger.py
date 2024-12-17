import os
import logging


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
    ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(
                name, output_format, output_file_path, level
            )
        return cls._instance

    def _initialize(self, name, output_format, output_file_path, level):
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
