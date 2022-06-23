import os
import logging
from logging.handlers import RotatingFileHandler
from loguru import logger as loguru_logger
from converge import settings


def build_api_logger():
    """
    Builds multiprocess-safe (hence loguru over stdlib logger) API logger
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


def build_app_logger(name='app', logfile='app.log', debug=True):
    """
    General purpose application logger. Useful mainly for debugging
    """
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logdir = 'logs'  # TODO: move this to settings
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    logpath = os.path.join(logdir, logfile)
    maxBytes = 1024 * 1024 * 10
    handler = RotatingFileHandler(logpath, maxBytes=maxBytes, backupCount=100)
    handler.setLevel(level)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


api_logger = build_api_logger() if settings.API_LOGGER.ENABLED else None
app_logger = build_app_logger()
