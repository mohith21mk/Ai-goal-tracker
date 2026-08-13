import logging
import sys
from ..config import settings

def setup_logger():
    logger = logging.getLogger("mkc_api")
    
    if logger.handlers:
        return logger

    # In production, use JSON or more structured logging
    # For now, we set up a stream handler that outputs clear info
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.ENVIRONMENT == "production":
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
    else:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()
