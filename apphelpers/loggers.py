import logging
from logging.handlers import SysLogHandler


def build_api_logger():
    level = settings.get('API_LOGGER.LEVEL', logging.INFO)
    port = settings.API_LOGGER.PORT
    rsyslog_server = settings.API_LOGGER.SYSLOG_SERVER
    api_logger = logging.getLogger('APILogger')
    api_logger.setLevel(level)
    handler = SysLogHandler(address=(rsyslog_server, port))
    formatter = logging.Formatter('| %(asctime)s | %(message)s')
    handler.setFormatter(formatter)
    api_logger.addHandler(handler)
    return api_logger


api_logger = build_api_logger() if settings.API_LOGGER.ENABLED else None
