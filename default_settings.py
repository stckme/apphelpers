DEBUG = True
DB_NAME = "defaultdb"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"

SESSIONSDB_HOST = "127.0.0.1"
SESSIONSDB_PORT = 6379
SESSIONSDB_PASSWD = None
SESSIONSDB_NO = 1

# SMTP
SMTP_HOST = "127.0.0.1"
SMTP_PORT = 10000
SMTP_USERNAME = None
SMTP_KEY = ""

HONEYBADGER_API_KEY = "secret"
HB_PARAM_FILTERS = ["password", "passwd", "secret"]


class API_LOGGER:
    ENABLED = False
