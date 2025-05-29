import logging
import os
import sys
from typing import Optional

def setup_production_logging() -> logging.Logger:
    """Set up production-ready logging with proper formatting and handlers."""
    logger = logging.getLogger("jh-market-data")
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level from environment or default to INFO
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create formatter for structured logging
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler for Vercel logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for local development
    if os.environ.get("NODE_ENV") != "production":
        try:
            file_handler = logging.FileHandler("market_data_service.log", mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

# Initialize logger
logger = setup_production_logging()
