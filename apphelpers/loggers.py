from logging.handlers import SysLogHandler
from loguru import logger as loguru_logger
from converge import settings

def build_api_logger():
    """
    Builds multiprocess-safe (hence loguru over stdlib logger) general purpose API logger
    """
    level = settings.API_LOGGER.LEVEL
    handler = settings.API_LOGGER.FILEPATH
    if handler:  # Else log to sys.stderr by default
        rotation = settings.API_LOGGER.ROTATION
        retention = settings.API_LOGGER.RETENTION
        loguru_logger.add(handler, retention=retention, rotation=rotation,
                          format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
                          enqueue=True, level=level)
    return loguru_logger


api_logger = build_api_logger() if settings.API_LOGGER.ENABLED else None
