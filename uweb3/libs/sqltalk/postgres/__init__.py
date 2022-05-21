#!/usr/bin/python
__author__ = 'Stef van Houten <stef@underdark.nl>'
__version__ = '0.1'

# Application specific modules
import psycopg2
from . import cursor
from . import connection

def Connect(*args, **kwargs) -> connection.Connection:
  """Factory function for connection.Connection."""
  return psycopg2.connect(connection_factory=connection.Connection, cursor_factory=cursor.Cursor, *args, **kwargs)  # type: ignore

