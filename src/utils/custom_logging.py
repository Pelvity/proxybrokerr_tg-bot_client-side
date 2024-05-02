# src/utils/custom_logging.py

import logging
from datetime import datetime

class WarsawTimeFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', timezone=None):
        super().__init__(fmt, datefmt, style)
        self.timezone = timezone

    def formatTime(self, record, datefmt=None):
        if self.timezone:
            ct = datetime.fromtimestamp(record.created, tz=self.timezone)
        else:
            ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.isoformat()
        return s

class CustomLoggingFilter(logging.Filter):
    def filter(self, record):
        return True
