from logging.handlers import SysLogHandler
from loguru import logger as loguru_logger
from converge import settings

def build_api_logger():
    level = settings.get('API_LOGGER.LEVEL', "INFO")
    port = settings.API_LOGGER.PORT
    rsyslog_server = settings.API_LOGGER.SYSLOG_SERVER
    handler = SysLogHandler(address=(rsyslog_server, port))
    loguru_logger.add(handler,
                      format="| {time:YYYY-MM-DD HH:mm:ss} | {message}",
                      level=level)
    return loguru_logger


api_logger = build_api_logger() if settings.API_LOGGER.ENABLED else None
