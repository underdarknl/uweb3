from .. import model

class User(model.BaseRecord):
  """ """
  def __init__(self, username=None, password=None, user_id=None):
    if user_id:
      self.user_id = user_id
    else:
      if not username or not password:
        raise ValueError("Username and password required")
      
      self.username = username
      self.password = password
  
  def FromName(self, connection, name):
    with connection as cursor:
      safe_name = connection.EscapeValues(name)
      user = cursor.Select(
          table='users',
          conditions='username="stef"')
    if not user:
      raise self.NotExistError('No user with name %r' % username)
    return user[0]