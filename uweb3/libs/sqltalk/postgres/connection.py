__author__ = 'Stef van Houten <stef@underdark.nl>'
__version__ = '0.1'

import psycopg2
import psycopg2.extras
from .. import sqlresult

class Connection:
  def __init__(self, user, password, host, port, database):
    self.connection = psycopg2.connect(dbname=database, user=user, password=password, host=host, port=port)
    self.cursor = self.connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)


  def __enter__(self):
    return self.cursor

  def __exit__(self, exc_type, exc_value, _exc_traceback):
    pass

  def Query(self, query_string):
    self.cursor.execute(query_string)
    results =  self.cursor.fetchall()
    if results:
      fields = list(results[0])
    else:
      fields = []
    return sqlresult.ResultSet(affected=self.cursor.rowcount,
                               fields=fields,
                               charset='utf-8',
                               insertid=self.cursor.lastrowid,
                               query=query_string,
                               result=results
    )

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
