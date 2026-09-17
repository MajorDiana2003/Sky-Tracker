import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Кастомный форматировщик для окрашивания логов в консоли."""

    RESET = "\033[0m"
    WHITE = "\033[37m"
    RED = "\033[31m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.WHITE
        if record.levelno > logging.INFO:
            color = self.RED

        formatter = logging.Formatter(f"{color}[%(levelname)s] %(asctime)s - %(message)s{self.RESET}")
        return formatter.format(record)


def setup_logger() -> logging.Logger:
    """Инициализация и настройка глобального логгера проекта."""
    logger = logging.getLogger("SkyTracker")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()
