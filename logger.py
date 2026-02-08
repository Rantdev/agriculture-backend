"""
Logging utilities for the backend
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def setup_logging(app, config):
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOGGING_CONFIG['file'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Remove default handler
    app.logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, config.LOGGING_CONFIG['level'].upper())
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        config.LOGGING_CONFIG['file'],
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    return app.logger

class AppLogger:
    """Centralized logging class"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def debug(self, message, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message, **kwargs):
        self.logger.critical(message, extra=kwargs)

def get_logger(name):
    """Get a logger instance"""
    return AppLogger(name)
