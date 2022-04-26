#!/usr/bin/python3
"""SQLTalk SQLite Cursor class."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.4'


# Custom modules
import sqlite3
from .. import sqlresult
from .. import base_cursor

class Cursor(base_cursor.BaseCursor):
  DatabaseError = sqlite3.DatabaseError
  DataError = sqlite3.DataError
  Error = sqlite3.Error
  IntegrityError = sqlite3.IntegrityError
  InterfaceError = sqlite3.InterfaceError
  InternalError = sqlite3.InternalError
  NotSupportedError = sqlite3.NotSupportedError
  OperationalError = sqlite3.OperationalError
  ProgrammingError = sqlite3.ProgrammingError
  Warning = sqlite3.Warning

  def __init__(self, connection):
    super().__init__(connection)
    self.connection = connection
    self.cursor = connection.cursor()

  def Execute(self, query, args=(), many=False):
    try:
      if many:
        result = self.cursor.executemany(query, args)
      else:
        result = self.cursor.execute(query, args)
    except Exception:
      self.connection.logger.exception('Exception during query execution')
      raise
    stored_result = self.cursor.fetchall()
    if stored_result:
      fields = list(stored_result[0])
    else:
      fields = []
    return sqlresult.ResultSet(
        affected=result.rowcount,
        charset='utf-8',
        fields=fields,
        insertid=result.lastrowid,
        query=(query, tuple(args)),
        result=stored_result
    )

  def Update(self, table, values, conditions, order=None,
             limit=None, offset=None, escape=True):
    """Updates table records to the new values where conditions are met.

    Arguments:
      table:      string. Name of table to update values in.
      values:     dictionary. Key for fieldname, value for content (autoquoted).
      conditions: string/list/tuple.
                  Where statements. Literal as string. AND'd if list/tuple.
                  THESE WILL NOT BE ESCAPED FOR YOU, EVER.
      order:      (nested) list/tuple (optional).
                  Defines sorting of table before updating, elements can be:
                    string: a field to order by (in default database order).
                    list/tuple of two elements:
                      1) string, field name to order by
                      2) bool, revserse; set this to True to reverse the order
      limit:      integer (optional). Defines max rows to update.
                  Default value for this is None, meaning no limit.
      offset:     integer (optional). Number of rows to skip, requires limit.
      escape:     boolean. Defines whether table names, fields and values should
                  be escaped. Set this to False if you want to make use of
                  MySQL functions on this query. Default True.

    Returns:
      sqlresult.ResultSet object.
    """
    if escape:
      field_escape = self.connection.EscapeField
      values = self.connection.EscapeValues(values)
    else:
      field_escape = lambda x: x
    return self._Execute('UPDATE %s SET %s WHERE %s %s %s' % (
        self._StringTable(table, field_escape),
        ', '.join('`%s`="%s"' % value for value in values.items()),
        self._StringConditions(conditions, field_escape),
        self._StringOrder(order, field_escape),
        self._StringLimit(limit, offset)))

  def Insert(self, table, values):
    if not values:
      raise ValueError('Must insert 1 or more value')
    elif isinstance(values, dict):
      query = ('INSERT INTO %s (%s) VALUES (%s)' %
               (table,
                ', '.join(map(self.connection.EscapeField, values)),
                ', '.join('?' * len(values))))
      return self.Execute(query, args=list(values.values()), many=False)
    query = ('INSERT INTO %s (%s) VALUES (%s)' %
             (table,
              ', '.join(map(self.connection.EscapeField, values[0])),
              ', '.join('?' * len(values[0]))))
    return self.Execute(
        query, args=(row.values() for row in values), many=True)


