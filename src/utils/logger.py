import logging
import os
from typing import Dict

class Logger:
    """A class that manages everything related to the Logs folder"""
    ENABLE_LOGGING = True
    WIPE_LOG_ON_STARTUP = True

    FOLDERNAME_LOGS = "logs"
    FILENAME_COMBAT_EVENT_LOG = "combat_events"
    FILENAME_OBJ_UPDATES_LOG = "obj_updates"

    _initialized_loggers: dict[str, logging.Logger] = {}

    @staticmethod
    def _setup(log_file_name: str) -> logging.Logger:
        """Helper method to set up logging configuration for a specific log file"""
        if log_file_name in Logger._initialized_loggers:
            return Logger._initialized_loggers[log_file_name]
        folder_name = Logger.FOLDERNAME_LOGS  # Create logs directory if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        logger = logging.getLogger(log_file_name)  # create named logger for this log file
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:  # prevent adding duplicate handlers
            path_name = os.path.join(folder_name, f"{log_file_name}.log")
            if Logger.WIPE_LOG_ON_STARTUP and os.path.exists(path_name):
                os.remove(path_name)  # wipe log file on startup if enabled
            file_handler = logging.FileHandler(path_name)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('(%(asctime)s) %(levelname)s: %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.propagate = False  # prevent propagation to root logger to avoid duplicate messages
        Logger._initialized_loggers[log_file_name] = logger
        if len(Logger._initialized_loggers) == 1:  # Log initialization message only once
            Logger.info("Game has been started.", Logger.FILENAME_OBJ_UPDATES_LOG)
        return logger

    @staticmethod
    def debug(message: str, log_file_name: str) -> None:
        """Log debug message to file only (no console output)"""
        logger = Logger._setup(log_file_name)
        logger.debug(message)

    @staticmethod
    def info(message: str, log_file_name: str) -> None:
        """Log info message to file and print to console"""
        logger = Logger._setup(log_file_name)
        print(message)
        logger.info(message)

    @staticmethod
    def warning(message: str, log_file_name: str) -> None:
        """Log warning message to file and print to console with Warning prefix"""
        logger = Logger._setup(log_file_name)
        print(f'Warning: {message}')
        logger.warning(message)

    @staticmethod
    def error(message: str, log_file_name: str) -> None:
        """Log error message to file and print to console with Error prefix"""
        logger = Logger._setup(log_file_name)
        print(f'Error: {message}')
        logger.error(message)

    @staticmethod
    def critical(message: str, log_file_name: str) -> None:
        """Log critical message to file and print to console with Critical prefix"""
        logger = Logger._setup(log_file_name)
        print(f'Critical: {message}')
        logger.critical(message)

    @staticmethod
    def print_only(message: str) -> None:
        """Print message to console only (no logging)"""
        print(message)