#!/usr/bin/python
__author__ = "Stef van Houten <stef@underdark.nl>"
__version__ = "0.1"

# Application specific modules
from . import connection


def Connect(*args, **kwargs):
    """Factory function for connection.Connection."""
    return connection.Connection(*args, **kwargs)
