import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure console and rotating-file logs."""
    settings = get_settings()
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=2_000_000,
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
