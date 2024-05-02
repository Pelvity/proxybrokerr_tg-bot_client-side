import logging
import pytz
from datetime import datetime

class CustomLoggingFilter(logging.Filter):
    def filter(self, record):
        record.client_ip = getattr(record, "client_ip", "unknown")
        record.client_username = getattr(record, "client_username", "unknown")
        record.user_message = getattr(record, "user_message", "unknown")
        return True
    

class WarsawTimeFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt):
        super().__init__(fmt, datefmt)
        self.converter = datetime.fromtimestamp
        self.warsaw_timezone = pytz.timezone("Europe/Warsaw")

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        ct = ct.replace(microsecond=0)
        ct = ct.astimezone(self.warsaw_timezone)
        return ct.strftime(datefmt) if datefmt else ct.isoformat()