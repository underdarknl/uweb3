#!/usr/bin/python3
"""SQLTalk SQLite Cursor class."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.4'


# Custom modules
import sqlite3
from .. import sqlresult

class Cursor:
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
    self.connection = connection
    self.cursor = connection.cursor()

  def _Execute(self, query):
    """Actually executes the query and returns the result of it.

    Arguments:
      @ query: basestring,
        Fully formatted sql statement to execute. In case of unicode, the
        string is encoded to the local character set before it is passed on
        to the server.

    Returns:
      sqlresult.ResultSet instance holding all query result data.
    """
    # TODO(Elmer): Fix this so that arguments can be given independent of the
    # query they belong to. This enables proper SelectTables and enables a host
    # of other escaping things to start working properly.
    #   Refer to MySQLdb.cursor code (~line 151) to see how this works.
    self._LogQuery(query)
    return self.connection.Query(query.strip(), self)

  def _LogQuery(self, query):
    connection = self.connection
    if not isinstance(query, str):
      query = str(query, connection.charset, errors='replace')
    connection.logger.debug(query)
    connection.queries.append(query)

  @staticmethod
  def _StringConditions(conditions, _unused_field_escape):
    if not conditions:
      return '1'
    elif not isinstance(conditions, str):
      return ' AND '.join(conditions)
    return conditions

  @staticmethod
  def _StringFields(fields, field_escape):
    if fields is None:
      return '*'
    elif isinstance(fields, str):
      return field_escape(fields)
    return ', '.join(field_escape(fields, True))

  @staticmethod
  def _StringGroup(group, field_escape):
    if group is None:
      return ''
    elif isinstance(group, str):
      return 'GROUP BY ' + field_escape(group)
    return 'GROUP BY ' + ', '.join(field_escape(group, True))

  @staticmethod
  def _StringLimit(limit, offset):
    if limit is None:
      return ''
    elif offset:
      return 'LIMIT %d OFFSET %d' % (limit, offset)
    return 'LIMIT %d' % limit

  @staticmethod
  def _StringOrder(order, field_escape):
    if order is None:
      return ''
    orders = []
    for rule in order:
      if isinstance(rule, str):
        orders.append(field_escape(rule))
      else:
        orders.append('%s %s' % (field_escape(rule[0]), ('', 'DESC')[rule[1]]))
    return 'ORDER BY ' + ', '.join(orders)

  @staticmethod
  def _StringTable(table, field_escape):
    if isinstance(table, str):
      return field_escape(table)
    return ', '.join(field_escape(table, True))

  def Execute(self, query, args=(), many=False):
    try:
      if many:
        result = self.cursor.executemany(query, args)
      else:
        result = self.cursor.execute(query, args)
    except Exception:
      self.connection.logger.exception('Exception during query execution')
      raise
    fieldnames = [field[0] for field in result.description] if result.description else None
    return sqlresult.ResultSet(
        affected=result.rowcount,
        charset='utf-8',
        fields=fieldnames,
        insertid=result.lastrowid,
        query=(query, tuple(args)),
        result=[dict(zip(fieldnames, row)) for row in result.fetchall()],
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
        ', '.join('`%s`=%s' % value for value in values.items()),
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


  def Select(self, table, fields=None, conditions=None, order=None,
             group=None, limit=None, offset=0, escape=True, totalcount=False,
             distinct=False):
    """Select fields from table that match the conditions, ordered and limited.

    Arguments:
      table:      string/list/tuple. Table(s) to select fields out of.
      fields:     string/list/tuple (optional). Fields to select. Default '*'.
                  As string, single field name. (autoquoted)
                  As list/tuple, one field name per element. (autoquoted)
                  If the fielname itself is supplied as a tuple,
                  `field` as `name' will be returned where name is the second
                  item in the tuple. (autoquoted)
      conditions: string/list/tuple (optional). SQL 'where' statement.
                  Literal as string. AND'd if list/tuple.
                  THESE WILL NOT BE ESCAPED FOR YOU, EVER.
      order:      (nested) list/tuple (optional).
                  Defines sorting of table before updating, elements can be:
                    string: a field to order by (in default database order).
                    list/tuple of two elements:
                      1) string, field name to order by
                      2) bool, revserse; set this to True to reverse the order
      group:      str (optional). Field name or function to group result by.
      limit:      integer (optional). Defines output size in rows.
      offset:     integer (optional). Number of rows to skip, requires limit.
      escape:     boolean. Defines whether table and field names should be
                  escaped. Set this to False if you want to make use of MySQL
                  functions on this query. Default True.
      totalcount: boolean. If this is set to True, queries with a LIMIT applied
                  will have the full number of matching rows on
                  the affected_rows attribute of the resultset.
      distinct:   bool (optional). Performs a DISTINCT query if set to True.

    Returns:
      sqlresult.ResultSet object.
    """
    field_escape = self.connection.EscapeField if escape else self.NoEscapeField
    result = self._Execute('SELECT %s %s %s FROM %s WHERE %s %s %s %s' % (
        'SQL_CALC_FOUND_ROWS' if totalcount and limit is not None else '',
        'DISTINCT' if distinct else '',
        self._StringFields(fields, field_escape),
        self._StringTable(table, field_escape),
        self._StringConditions(conditions, field_escape),
        self._StringGroup(group, field_escape),
        self._StringOrder(order, field_escape),
        self._StringLimit(limit, offset)))
    if totalcount and limit is not None:
      result.affected = self._Execute('SELECT FOUND_ROWS()')[0][0]
    return result