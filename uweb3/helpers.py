from contextlib import contextmanager


@contextmanager
def transaction(connection, cls):
  """Start a transaction in which autocommit is turned off.
  If no error occurs during the transaction the session will be committed to the database (setting autocommit to true also commits),
  and autocommit is restored to True.
  If any (unhandled) Exception occurs the transaction is rolled back and the exception is propagated.

  Arguments:
    @ connection: The databaseconnection available in the PageMaker class.
    @ cls: uweb3.model.BaseRecord
      Any class that derives from the BaseRecord class.
  """
  try:
    cls.autocommit(connection, False)
    yield # The contextmanager requires us to yield.
  except Exception as e:
    cls.rollback(connection)
    raise e
  finally:
    cls.autocommit(
        connection, True
    )  # This is important, if we do not turn this back on connection will not commit any queries in other requests.
