from .. import model

class User(model.BaseRecord):
  """ """
  def __init__(self):
    pass
  
  def FromName(self, connection, name):
    with connection as cursor:
      safe_name = connection.EscapeValues(name)
      user = cursor.Select(
          table='users',
          conditions='username="stef"')
    if not user:
      raise self.NotExistError('No user with name %r' % username)
    return user[0]