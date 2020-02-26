import hashlib

import bcrypt

from .. import model

class UserCookieInvalidError(Exception):
  """Superclass for errors returned by the user class."""  

class Test(model.SettingsManager):
  """ """

class UserCookie(model.SecureCookie):
  """ """

class Users(model.Record):
  """ """
  salt = "SomeSaltyBoi"
  cookie_salt = "SomeSaltyCookie"
  
  UserCookieInvalidError = UserCookieInvalidError

  @classmethod
  def CreateNew(cls, connection, user):
    """Creates new user if not existing
    
    Arguments:
      @ connection: sqltalk database connection object
      @ user: dict. username and password keys are required.   
    Returns:
      ValueError: if username/password are not set
      AlreadyExistsError: if username already in database
      Users: Users object when user is created
    """
    if not user.get('username'):
      raise ValueError('Username required')
    if not user.get('password'):
      raise ValueError('Password required')

    try:
      cls.FromName(connection, user.get('username'))
      return cls.AlreadyExistError("User with name '{}' already exists".format(user.get('username')))
    except cls.NotExistError:
      user['password'] = cls.__HashPassword(user.get('password')).decode('utf-8')
      return cls.Create(connection, user)
        
  @classmethod
  def FromName(cls, connection, username):
    """Select a user from the database based on name
    Arguments:
      @ username: str
    Returns:
      NotExistError: raised when no user with given username found
      Users: Users object with the connection and all relevant user data
    """
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
    """Check if passwords match
    
    Arguments:
      @ password: str
      @ hashed: str password hash from users database table
    Returns:
      Boolean: True if match False if not
    """
    if not isinstance(hashed, bytes):
      hashed = hashed.encode('utf-8')
      
    password = password + cls.salt
    return bcrypt.checkpw(password.encode('utf-8'), hashed)
  
  @classmethod
  def CreateValidationCookieHash(cls, data):
    """Takes a non nested dictionary and turns it into a secure cookie.
  
    Required:
      @ id: str/int 
    Returns:
      A string that is ready to be placed in a cookie. Hash and data are seperated by a + 
    """
    if not data.get('id'):
      raise ValueError("id is required")
    
    cookie_dict = {}
    string_to_hash = ""
    for key in data.keys():
      if not isinstance(data[key], (str, int)):
        raise ValueError('{} must be of type str or int'.format(data[key]))
      value = str(data[key])
      string_to_hash += value
      cookie_dict[key] = value
      
    hashed = (string_to_hash + cls.cookie_salt).encode('utf-8')
    h = hashlib.new('ripemd160')
    h.update(hashed)
    return '{}+{}'.format(h.hexdigest(), cookie_dict)
  
  @classmethod
  def ValidateUserCookie(cls, cookie):
    """Takes a cookie and validates it
    Arguments
      @ str: A hashed cookie from the `CreateValidationCookieHash` method 
    """
    from ast import literal_eval
    if not cookie:
      return None
    
    try:
      data = cookie.rsplit('+', 1)[1]
      data = literal_eval(data)
    except Exception:
      raise cls.UserCookieInvalidError("Invalid cookie")
    
    user_id = data.get('id', None)
    if not user_id:
      raise cls.UserCookieInvalidError("Could not get id from cookie")
    
    if cookie != cls.CreateValidationCookieHash(data):
      raise cls.UserCookieInvalidError("Invalid cookie")
    
    return user_id
  