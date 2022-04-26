#!/usr/bin/python3
"""This module implements the Connection class, which sets up a connection to
an SQLite database. From this connection, cursor objects can be created, which
use the escaping and character encoding facilities offered by the connection.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.3'

# Standard modules
import sqlite3
import logging
import os
import queue
import threading

# Application specific modules
from . import cursor
from .. import sqlresult

COMMIT = '----COMMIT'
ROLLBACK = '----ROLLBACK'
NAMED_TYPE_SELECT = 'SELECT `name` FROM `sqlite_master` where `type`=?'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class Connection(sqlite3.Connection):
  def __init__(self, *args, **kwds):
    db_name = os.path.splitext(os.path.split(args[0])[1])[0]
    self.logger = logging.getLogger('sqlite_%s' % db_name)
    self.counter_transactions = 0
    self.counter_queries = 0
    self.charset = 'utf-8'
    self.queries = []
    if kwds.pop('debug', False):
      self.logger.setLevel(logging.DEBUG)
    else:
      self.logger.setLevel(logging.WARNING)
    if kwds.pop('disable_log', False):
      self.logger.disable_logger = True
    self.autocommit_mode = kwds.pop('autocommit', True)
    sqlite3.Connection.__init__(self, *args, **kwds)
    self.row_factory = dict_factory

  def __enter__(self):
    """Starts a transaction."""
    self.logger.debug('Beginning new transaction.')
    return cursor.Cursor(self)

  def __exit__(self, exc_type, _exc_value, _exc_traceback):
    """End of transaction: commits , or rolls back on failure."""
    if exc_type:
      self.rollback()
      self.logger.warning('Transaction was rolled back.')
    elif self.autocommit_mode:
      self.commit()
      self.logger.debug('Transaction committed.')

  def autocommit(self, value):
    self.autocommit_mode = value

  def commit(self):
    sqlite3.Connection.commit(self)

  def rollback(self):
    sqlite3.Connection.rollback(self)

  def EscapeField(self, field, multiple=False):
    """Returns a SQL escaped field or table name.

    Set multiple = True if field is a tuple of names to be escaped.
    If multiple = False, and a tuple is encountered `field` as `name` will be
      returned where the second part of the tuple is the `name` part.
    """
    if not field:
      return ''
    if isinstance(field, str):
      fields = '.'.join('`%s`' % f.replace('`', '``') for f in field.split('.'))
      return fields.replace('`*`', '*')
    elif not multiple and isinstance(field, tuple):
      return '%s as %s' % (self.EscapeField(field[0]), self.EscapeField(
          field[1]))
    return map(self.EscapeField, field)

  def EscapeValues(self, obj):
    """We do not escape here, we simple return the value and allow the query
    engine to escape using parameters.
    """
    if isinstance(obj, str):
      return f'"{obj}"' # XXX: This isn't really clean.
    return obj

  def ShowTables(self):
    result = self.execute(NAMED_TYPE_SELECT, ('table',)).fetchall()
    return [row[0] for row in result]

  def Query(self, query_string, cur=None):
    self.counter_queries += 1
    # if isinstance(query_string, str):
    #   query_string = query_string.encode(self.charset)
    if not cur:
      cur = cursor.Cursor(self)
    return cur.Execute(query_string)


class ThreadedConnection(threading.Thread):
  def __init__(self, *args, **kwds):
    super(ThreadedConnection, self).__init__()
    # Set up a logger
    db_name = os.path.splitext(os.path.split(args[0])[1])[0]
    self.logger = logging.getLogger('sqlite_%s' % db_name)
    if kwds.pop('debug', False):
      self.logger.setLevel(logging.DEBUG)
    else:
      self.logger.setLevel(logging.WARNING)
    if kwds.pop('disable_log', False):
      self.logger.disable_logger = True

    self.sqlite_args = args
    self.sqlite_kwds = kwds
    self.queries = queue.queue(1)
    self.transaction_lock = threading.RLock()
    self.daemon = True
    self.start()

  def __enter__(self):
    """Starts a transaction."""
    self.transaction_lock.acquire()
    return cursor.Cursor(self)

  def __exit__(self, exc_type, _exc_value, _exc_traceback):
    """End of transaction: commits, or rolls back on failure."""
    if exc_type:
      self.rollback()
      self.logger.warning('Transaction was rolled back.')
    else:
      self.commit()
      self.logger.debug('Transaction committed.')
    self.transaction_lock.release()

  def commit(self):
    self.execute(COMMIT)

  def execute(self, query, args=()):
    with self.transaction_lock:
      response = queue.queue()
      self.queries.put((query, args, response, False))
      return self._ProcessResponse(response)

  def executemany(self, query, args=()):
    with self.transaction_lock:
      response = queue.queue()
      self.queries.put((query, args, response, True))
      return self._ProcessResponse(response)

  def rollback(self):
    self.execute(ROLLBACK)

  def run(self):
    connection = Connection(*self.sqlite_args, **self.sqlite_kwds)
    while True:
      query, args, response, many = self.queries.get()
      try:
        if query is COMMIT:
          response.put(connection.commit())
        elif query is ROLLBACK:
          response.put(connection.rollback())
        else:
          execute = connection.executemany if many else connection.execute
          result = execute(query, args)
          response.put(SqliteResult(result.fetchall(), result.description,
                                    result.rowcount, result.lastrowid))
          del execute, result
      except Exception as error:
        response.put(error)
        del error

  @staticmethod
  def _ProcessResponse(response):
    """Processes the response given by the SQLite connection thread.

    If the response is an exception type, it will be raised in this thread, so
    that the underlying thread doesn't silently fail. This allows a database
    error to be handled by the calling code properly.
    """
    response = response.get()
    if isinstance(response, Exception):
      raise response
    return response

  @staticmethod
  def EscapeField(field):
    """Returns a SQL escaped field or table name."""
    return '.'.join('`%s`' % f.replace('`', '``') for f in field.split('.'))

  def ShowTables(self):
    result = self.execute(NAMED_TYPE_SELECT, ('table',)).fetchall()
    return [row[0] for row in result]


class SqliteResult:
  def __init__(self, result, description, rowcount, lastrowid):
    self.result = result
    self.description = description
    self.rowcount = rowcount
    self.lastrowid = lastrowid

  def fetchall(self):
    return self.result


#FIXME(Elmer): This needs defining in one place, not in each and every file.
DataError = sqlite3.DataError
DatabaseError = sqlite3.DatabaseError
Error = sqlite3.Error
IntegrityError = sqlite3.IntegrityError
InterfaceError = sqlite3.InterfaceError
InternalError = sqlite3.InternalError
NotSupportedError = sqlite3.NotSupportedError
OperationalError = sqlite3.OperationalError
