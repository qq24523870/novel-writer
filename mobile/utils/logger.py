import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

_logger_instance = None

def _ensure_log_dir(log_dir):
    if os.path.exists(log_dir):
        return log_dir
    try:
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except Exception:
        fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "logs")
        try:
            os.makedirs(fallback, exist_ok=True)
        except Exception:
            fallback = "/tmp/logs"
            os.makedirs(fallback, exist_ok=True)
        return fallback

def get_logger():
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    log_dir = _ensure_log_dir("logs")
    log_file = os.path.join(log_dir, f"novel_writer_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger("NovelWriter")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger_instance = logger
    return logger

logger = get_logger()
