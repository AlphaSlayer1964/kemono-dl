import logging

logger = logging.getLogger("kemono_dl")
logger.setLevel(logging.DEBUG)  # Or INFO, WARNING, etc.

# Optional: Add a default handler if no handlers are present
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
