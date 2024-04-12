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
        self.setup()
        
    def setup(self):
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






