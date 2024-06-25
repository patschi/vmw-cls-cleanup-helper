#!/usr/bin/env python3
from datetime import datetime
from os import environ

# Constants
debug = environ.get('CLEANUP_SCRIPT_DEBUG', 'false').lower() == 'true'


# Basic logging function
def log(sev: str, msg: str) -> None:
    """
    Basic logging function. Prints a message with a timestamp and severity level.
    :param sev: The severity level of the message (info, warning, error)
    :param msg: The message to print
    """
    severity = sev.upper()
    if not debug and severity == 'DEBUG':
        return
    date = datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')
    print('[{0}] [{1: <5s}] {2}'.format(date, severity, msg))

    if severity == 'ERROR':
        raise Exception(msg)
