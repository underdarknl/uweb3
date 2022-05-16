__author__ = 'Stef van Houten <stef@underdark.nl>'
__version__ = '0.1'

import psycopg2
import psycopg2.extras
from .. import sqlresult

class Connection:
  def __init__(self, user, password, host, port, database):
    self.connection = psycopg2.connect(dbname=database, user=user, password=password, host=host, port=port)

  def __enter__(self):
    return self.connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

  def __exit__(self, exc_type, exc_value, _exc_traceback):
    self.commit()

  def commit(self):
    self.connection.commit()

  def rollback(self):
    self.connection.rollback()

  def autocommit(self, value):
    self.connection.autocommit = value

  def CurrentDatabase(self):
    """Return the name of the currently used database"""
    return self.Query('SELECT current_database()')[0]['current_database']

  def Query(self, query_string):
    with self as cursor:
      cursor.execute(query_string)
      results =  cursor.fetchall()
      if results:
        fields = list(results[0])
      else:
        fields = []
      return sqlresult.ResultSet(affected=cursor.rowcount,
                                fields=fields,
                                charset=self.connection.encoding,
                                insertid=cursor.lastrowid,
                                query=query_string,
                                result=results
    )

  def Info(self):
    return {
        'db': self.CurrentDatabase(),
        'charset': self.connection.encoding,
        'server': self.connection.server_version,
        # 'debug': self.debug,
        'autocommit': self.connection.autocommit,
        # 'querycount': self.counter_queries,
        # 'transactioncount': self.counter_transactions
    }

  Error = psycopg2.Error
  InterfaceError = psycopg2.InterfaceError
  DatabaseError = psycopg2.DatabaseError
  DataError = psycopg2.DataError
  OperationalError = psycopg2.OperationalError
  IntegrityError = psycopg2.IntegrityError
  InternalError = psycopg2.InternalError
  ProgrammingError = psycopg2.ProgrammingError
  NotSupportedError = psycopg2.NotSupportedError
  Warning = psycopg2.Warning
