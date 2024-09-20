import os
import logging

class SystemLogger:
    def __init__(self, name: str, output_format: str = "file", output_file_path: str = "", level: int = logging.INFO):
        """
        Initialize a SystemLogger instance.

        Parameters:
        - name (str): The name of the logger.
        - output_format (str): The output destination for the logger ('file', 'terminal', or 'both').
        - output_file_path (str): The path for the output file. If output format 'terminal' will be ignored
        - level (int): The logging level.
        """
        # Validate the output format
        if output_format not in ["file", "terminal", "both"]:
            raise ValueError("Invalid output_format. Choose 'file', 'terminal', or 'both'.")

        self.name = name
        self.level = level
        self.output_format = output_format.lower()
        self.output_file_path =  output_file_path
        self.logger = logging.getLogger(f'{self.name}_logger')
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
        # Set log level
        self.logger.setLevel(self.level)
        
        # Prevents the log messages from being passed to the root logger
        self.logger.propagate = False  

        # Create the log directory if it doesn't exist
        if self.output_format in ["file", "both"]:
            if not os.path.exists(self.output_file_path):
                os.makedirs(self.output_file_path, exist_ok=True)

            log_file_name = os.path.join(self.output_file_path, f'{self.name}.log')

        # Check for and remove existing handlers to prevent duplicates
        self.logger.handlers = [h for h in self.logger.handlers if not isinstance(h, (logging.FileHandler, logging.StreamHandler))]

        # Configure file handler
        if self.output_format in ["file", "both"]:
            file_handler = logging.FileHandler(log_file_name, mode='w')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)

        # Configure terminal handler
        if self.output_format in ["terminal", "both"]:
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


        # # Define the log directory path
        # base_dir = os.getcwd()
        # log_dir = os.path.join(base_dir, self.strategy_name, 'logs')

        # # Create the log directory if it doesn't exist
        # if not os.path.exists(log_dir) and self.output in ["file", "both"]:
        #     os.makedirs(log_dir)

        # log_file_name = os.path.join(log_dir, f'{self.strategy_name}.log')
        
        # # Check for and remove existing handlers to prevent duplicates
        # self.logger.handlers = [h for h in self.logger.handlers if not isinstance(h, (logging.FileHandler, logging.StreamHandler))]

        # # Configure file handler
        # if self.output in ["file", "both"]:
        #     file_handler = logging.FileHandler(log_file_name, mode='w')
        #     file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        #     self.logger.addHandler(file_handler)

        # # Configure terminal handler
        # if self.output in ["terminal", "both"]:
        #     stream_handler = logging.StreamHandler()
        #     stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        #     self.logger.addHandler(stream_handler)

        # self.logger.info("Logger setup complete.")




