import logging
import sys

from src.utils.constants import PROJECT_ROOT
from src.utils.config import config


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Настраивает и возвращает логгер"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if config.log_to_file:
        log_file = PROJECT_ROOT / 'logs' / 'app.log'
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


server_logger = setup_logger('server')
client_logger = setup_logger('client')
