#!/usr/bin/env python3
from datetime import datetime
from os import environ

# Only check local timezone if not running in a container, otherwise use UTC
# Check if tzlocal is available, otherwise use pytz as a fallback with UTC
try:
    import tzlocal

    local_timezone = tzlocal.get_localzone()
except ImportError:
    import pytz

    local_timezone = pytz.timezone('UTC')

# Constants
debug = environ.get('CLEANUP_SCRIPT_DEBUG', 'false').lower() == 'true'


# Basic logging function
def log(severity: str, msg: str) -> None:
    """
    Basic logging function. Prints a message with a timestamp and severity level.
    :param severity: The severity level of the message (info, warning, error)
    :param msg: The message to print
    """
    severity = severity.upper()
    if not debug and severity == 'DEBUG':
        return
    date = datetime.now(tz=local_timezone).strftime('%Y-%m-%dT%H:%M:%S%z')
    print('[{0}] [{1: <5s}] {2}'.format(date, severity, msg))

    if severity == 'ERROR':
        raise Exception(msg)
