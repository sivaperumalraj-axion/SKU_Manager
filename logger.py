import logging
import os

LOG_DIR = "logs"
LOG_FILE = "execution.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger():
    """Configures and returns the logger."""
    logger = logging.getLogger("UniversalRunner")
    logger.setLevel(logging.DEBUG)

    # File Handler
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console Handler (Optional, for debugging the app itself)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Avoid adding duplicate handlers if setup is called multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def get_log_file_path():
    """Returns the absolute path to the log file."""
    return os.path.abspath(LOG_PATH)

def clear_logs():
    """Clears the log file content."""
    with open(LOG_PATH, 'w'):
        pass
