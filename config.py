from os import environ
from dotenv import load_dotenv
load_dotenv(".env")

CONF_API = environ.get("CONF_API")
TELEGRAM_KEY = environ.get("TELEGRAM_KEY")
