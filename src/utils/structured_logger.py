"""
Structured JSON logger with color support for console output
"""

import structlog
import logging
import sys
from typing import Optional
from src.core.constants import LOG_LEVEL, LOG_FORMAT


def setup_logger(
    name: str = __name__,
    level: Optional[str] = None,
    log_format: Optional[str] = None
) -> structlog.BoundLogger:
    """Setup structured logger with JSON formatting"""
    
    level = level or LOG_LEVEL
    log_format = log_format or LOG_FORMAT
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level),
    )
    
    return structlog.get_logger(name)


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get or create logger instance"""
    return structlog.get_logger(name)