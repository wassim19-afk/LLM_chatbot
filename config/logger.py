# config/logger.py
# Centralized logging configuration for the application.
# All modules should use the logger from this module for consistent logging.

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_level: int = logging.WARNING) -> logging.Logger:
    """
    Setup and return a logger with standard configuration.
    
    Args:
        name (str): Logger name (usually __name__ of the module)
        log_level (int): Logging level (default: WARNING)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # File handler with rotation (max 5 MB per file, keep 7 days worth)
    log_file = os.path.join(log_dir, "chatbot.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=7  # Keep 7 rotated files
    )
    file_handler.setLevel(log_level)
    
    # Console handler for real-time monitoring
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Format: [timestamp] LEVEL: message
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Create application-level loggers
def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name."""
    return setup_logger(name, log_level=logging.WARNING)
