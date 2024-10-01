import os
import logging


class SystemLogger:
    _instance = None

    def __new__(
        cls,
        name="system",
        output_format="file",
        output_file_path="",
        level=logging.INFO,
    ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(
                name, output_format, output_file_path, level
            )
        return cls._instance

    def _initialize(self, name, output_format, output_file_path, level):
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
        if cls._instance is None:
            raise RuntimeError(
                "SystemLogger is not initialized. Call the constructor first."
            )
        return cls._instance.logger
