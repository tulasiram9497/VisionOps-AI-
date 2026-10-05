from __future__ import annotations

import logging


def configure_logging(level_name: str = "INFO") -> logging.Logger:
    """Initialize application logging."""
    logger = logging.getLogger("visionops")
    logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(handler)
    return logger


logger = configure_logging()
