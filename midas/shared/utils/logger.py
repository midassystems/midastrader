import os
import logging

class SystemLogger:
    def __init__(self, strategy:str, output: str = "file", level: int = logging.INFO):
        """
        Initialize a SystemLogger instance.

        Parameters:
        - strategy (str): The name of the strategy for which the logger is created.
        - output (str): The output destination for the logger ('file', 'terminal', or 'both').
        - level (int): The logging level.
        """
        self.strategy_name = strategy
        self.output = output.lower()
        self.level = level
        self.logger = logging.getLogger(f'{self.strategy_name}_logger')
        self._setup()
        
    def _setup(self):
        """
        Configures the logger with specified settings for file and/or terminal output.
        
        It performs the following tasks:
        - Sets the logger's level to the provided verbosity level.
        - Stops log messages from being propagated to the root logger.
        - Constructs the directory path for log files based on the strategy name.
        - Creates the directory if it does not exist, provided the output includes file logging.
        - Sets up file and terminal handlers with appropriate formatting, creating log files or terminal logs as specified.

        The method ensures that if handlers of the type `logging.FileHandler` or `logging.StreamHandler` already exist, they are removed to prevent duplicate logging.

        Note:
            This method is intended to be called internally by the `__init__` method during the initialization of a `SystemLogger` instance and should not be called directly.
        """
        self.logger.setLevel(self.level)
        self.logger.propagate = False  # Prevents the log messages from being passed to the root logger

        # Define the log directory path
        base_dir = os.getcwd()
        log_dir = os.path.join(base_dir, self.strategy_name, 'logs')

        # Create the log directory if it doesn't exist
        if not os.path.exists(log_dir) and self.output in ["file", "both"]:
            os.makedirs(log_dir)

        log_file_name = os.path.join(log_dir, f'{self.strategy_name}.log')
        
        # Check for and remove existing handlers to prevent duplicates
        self.logger.handlers = [h for h in self.logger.handlers if not isinstance(h, (logging.FileHandler, logging.StreamHandler))]

        # Configure file handler
        if self.output in ["file", "both"]:
            file_handler = logging.FileHandler(log_file_name, mode='w')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)

        # Configure terminal handler
        if self.output in ["terminal", "both"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(stream_handler)

        self.logger.info("Logger setup complete.")

    def log_dataframe(self,logger, df):
        """
        Log a DataFrame with consistent indentation.
        """
        message = df.to_string()
        padding = " "* 40   # Adjust this padding to align with the timestamp and other info
        message = padding + message.replace("\n", "\n"+padding)
        logger.info(message)






