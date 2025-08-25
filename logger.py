import logging
import os
from rich.logging import RichHandler

def setup_logger():
    log_level = os.getenv("GITBRIDGE_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    return logging.getLogger("gitbridge")