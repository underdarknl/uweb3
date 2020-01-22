import hashlib

import bcrypt

from .. import model

class UserCookieInvalidError(Exception):
  """Superclass for errors returned by the user class."""  

class Users(model.Record):
  """ """
  salt = "SomeSaltyBoi"
  UserCookieInvalidError = UserCookieInvalidError
  
  def __init__(self, username=None, password=None, 
               user_id=None, generateHash=True
               ):
    """Instantiate a User class. Username/password or user_id is required"""
    self.user_id = user_id
    self.username = username
    self.password = password
    #Check if username/password are set if no userid is supplied
    if not username and not user_id or not password and not user_id:
      raise ValueError("Username and password required")

    if username and password:
      if generateHash:
        self.hashed_password = self.HashPassword()

  def __str__(self):
    """Return user object as str"""
    return str({key: self.__dict__[key] for key in self.__dict__.keys() if key is not 'salt'})
  
  def __eq__(self, other):
    """Check if either passwords match or user_ids are equal"""
    #If both objects have an id compare the ids
    if self.user_id and other.user_id:
      return self.user_id == other.user_id
    
    is_match = self.ComparePassword(other.password)
    
    if is_match:
      self.user_id = other.user_id
      self.cookie = self._generateCookie(self.user_id)
      
    return is_match
  
  def Create(self, connection):
    try:
      self.FromName(connection)
      return self.AlreadyExistError("User with name '{}' already exists".format(self.username))
    except self.NotExistError:
      with connection as cursor:
        cursor.Insert('users', {
                                'username': self.username, 
                                'password': self.hashed_password.decode('utf-8')
                                })
  
  def FromName(self, connection):
    """Select a user from the database based on name"""
    with connection as cursor:
      safe_name = connection.EscapeValues(self.username)
      user = cursor.Select(
          table='users',
          conditions='username={}'.format(safe_name))
    if not user:
      raise self.NotExistError('No user with name %r' % self.username)
    return Users(user[0]['username'], user[0]['password'], user[0]['id'], generateHash=False)

  def HashPassword(self):
    """Hash password with bcrypt"""
    password = self.password + self.salt
    
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
  
  def ComparePassword(self, hashed):
    """Check if passwords match"""
    if not isinstance(hashed, bytes):
      hashed = hashed.encode('utf-8')
    password = self.password + self.salt
    
    return bcrypt.checkpw(password.encode('utf-8'), hashed)
  
  def _generateCookie(self, user_id):
    if not isinstance(user_id, bytes):
      hash = '{}{}'.format(user_id, self.salt).encode('utf-8')
      
    h = hashlib.new('ripemd160')
    h.update(hash)
    return '{}+{}'.format(h.hexdigest(), {'id': user_id})
 
  @classmethod
  def validateCookie(cls, cookie):
    from ast import literal_eval
    
    try:
      hashed, data = cookie.rsplit('+', 1)
      data = literal_eval(data)
      user_id = data.get('id', None)
    except Exception:
      raise cls.UserCookieInvalidError("Invalid cookie")

    if not user_id:
      raise cls.UserCookieInvalidError("Could not get id from cookie")
    if cookie != cls._generateCookie(cls, str(user_id)):
      raise cls.UserCookieInvalidError("Invalid cookie")
    
    return Users(user_id=user_id)
  