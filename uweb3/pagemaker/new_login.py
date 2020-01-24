import hashlib

import bcrypt

from .. import model

class UserCookieInvalidError(Exception):
  """Superclass for errors returned by the user class."""  

class Users(model.Record):
  """ """
  salt = "SomeSaltyBoi"
  UserCookieInvalidError = UserCookieInvalidError

  @classmethod
  def CreateNew(cls, connection, username, password):
    try:
      cls.FromName(connection, username)
      return cls.AlreadyExistError("User with name '{}' already exists".format(username))
    except cls.NotExistError:
      password = cls.__HashPassword(password).decode('utf-8')
      return cls.Create(connection, {
                              'username': username, 
                              'password': password,
                              })
        
  @classmethod
  def FromName(cls, connection, username):
    """Select a user from the database based on name"""
    with connection as cursor:
      safe_name = connection.EscapeValues(username)
      user = cursor.Select(
          table='users',
          conditions='username={}'.format(safe_name))
    if not user:
      raise cls.NotExistError('No user with name {}'.format(username))
    return cls(connection, user[0])


  @classmethod
  def __HashPassword(cls, password):
    """Hash password with bcrypt"""
    password = password + cls.salt
    
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
  
  @classmethod
  def ComparePassword(cls, password, hashed):
    """Check if passwords match"""
    if not isinstance(hashed, bytes):
      hashed = hashed.encode('utf-8')
      
    password = password + cls.salt
    return bcrypt.checkpw(password.encode('utf-8'), hashed)
  
  @classmethod
  def CreateValidationCookieHash(cls, user_id):
    if not isinstance(user_id, str):
      raise ValueError('UserID must be a string')
    
    hashed = (user_id + cls.salt).encode('utf-8')
    h = hashlib.new('ripemd160')
    h.update(hashed)
    return '{}+{}'.format(h.hexdigest(), { 
                                          'id': user_id,
                                          })

  @classmethod
  def CreateCRSFToken(cls, userInput):
    hashed = (userInput + cls.salt).encode('utf-8')
    h = hashlib.new('ripemd160')
    h.update(hashed)
    return h.hexdigest()
  
  @classmethod
  def ValidateUserCookie(cls, cookie):
    from ast import literal_eval
    
    if not cookie:
      return None
    
    try:
      data = cookie.rsplit('+', 1)[1]
      data = literal_eval(data)
      user_id = data.get('id', None)
    except Exception:
      raise cls.UserCookieInvalidError("Invalid cookie")

    if not user_id:
      raise cls.UserCookieInvalidError("Could not get id from cookie")
    if cookie != cls.CreateValidationCookieHash(str(user_id)):
      raise cls.UserCookieInvalidError("Invalid cookie")
    
    return user_id
  