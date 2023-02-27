from os import environ
from dotenv import load_dotenv
load_dotenv(".env")

CONF_ADDRESS = environ.get("CONF_ADDRESS")
CONF_API = CONF_ADDRESS + '/rest/api'
TELEGRAM_KEY = environ.get("TELEGRAM_KEY")
CALENDAR_PAGE = environ.get("CALENDAR_PAGE_ID")

CONF_LOGIN = environ.get("CONF_LOGIN")
CONF_PASSWORD = environ.get("CONF_PASSWORD")

DB_HOST = environ.get("DB_HOST")
DB_PORT = environ.get("DB_PORT")
