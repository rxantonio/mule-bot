import logging
from logging.handlers import RotatingFileHandler

# 1. Define the Filter Class
class WebexNoiseFilter(logging.Filter):
    def filter(self, record):
        # List of specific phrases you want to hide
        blocked_phrases = [
            "Your bot is open to anyone on Webex Teams",
            "Message is from myself"
        ]
        # Get the actual log message text
        message = record.getMessage()
        
        # If any blocked phrase is in the message, return False (drops the log)
        for phrase in blocked_phrases:
            if phrase in message:
                return False
        return True

def setup_logger(name=None, log_file='mule_bot_log.log', level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] : %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (Rotating)
    if log_file:
        fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=1)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # 2. Apply the Filter to the webex_bot logger
    webex_bot_logger = logging.getLogger('webex_bot')
    webex_bot_logger.addFilter(WebexNoiseFilter())

    # Still keep the general silencing for the websocket "heartbeats"
    logging.getLogger('webex_websocket_client').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)

    return logger