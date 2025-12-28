import logging
import sys
import json
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime
from core.config import config


class ColoredFormatter(logging.Formatter):
    """Custom formatter с цветове за console output (development only)"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.RESET}"
            )
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Production-grade JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from LogRecord
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with console and file handlers
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Избягваме дублиране на handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = level or config.get("logging.level", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Determine if we're in production
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    log_format = config.get("logging.format", "text" if not is_production else "json")
    
    # Console handler
    if config.get("logging.console_output", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if is_production and log_format == "json":
            # JSON format for production
            formatter = JSONFormatter()
        else:
            # Colored format for development
            formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file_path = log_file or config.get("logging.file", "logs/gpu_service.log")
    if log_file_path:
        # Ensure log directory exists
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=config.get("logging.max_bytes", 10485760),  # 10MB
            backupCount=config.get("logging.backup_count", 5),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Always use JSON format in files for production
        if is_production or log_format == "json":
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Pre-configured loggers за различни модули
def get_logger(name: str) -> logging.Logger:
    """Get or create logger for a module"""
    return setup_logger(name)


# Example usage loggers
scraper_logger = get_logger("scraper")
api_logger = get_logger("api")
storage_logger = get_logger("storage")
pipeline_logger = get_logger("pipeline")