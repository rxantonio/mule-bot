import logging
import os

def setup_logger(name=None, log_file='mule_bot_log.log', level=logging.INFO):
    """Set up console logging; file logging is currently disabled below."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] : %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File logging is disabled for the Kubernetes deployment. The console
    # handler above writes to stderr, which Kubernetes captures for kubectl logs.
    # Keep this block commented so file logging can be restored later if useful.
    # if log_file:
    #     fh = logging.FileHandler(log_file)
    #     fh.setFormatter(formatter)
    #     logger.addHandler(fh)

    return logger
