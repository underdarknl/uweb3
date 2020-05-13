#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

from uweb3 import SqAlchemyPageMaker
from uweb3.alchemy_model import AlchemyRecord
from uweb3.pagemaker.new_decorators import checkxsrf

from sqlalchemy import Column, Integer, String, update, MetaData, Table, ForeignKey, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, lazyload
from uweb3 import model
Base = declarative_base()

import hashlib
import bcrypt

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
    from sqlalchemy import Table, MetaData, Column, Integer, String, text
    meta = MetaData()
    users_table = Table('users', meta,
                        Column('id', Integer, primary_key=True),
                        Column('username', String(255)),
                        Column('password', String(255)),
                        )
    # result = connection.execute(users_table.select())
    # statement = text("SELECT * FROM users WHERE username = :name")
    # user = connection.execute(statement, {'name': username}).fetchone()
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

class User(AlchemyRecord, Base):
  __tablename__ = 'alchemy_users'

  id = Column(Integer, primary_key=True)
  username = Column(String, nullable=False, unique=True)
  password = Column(String, nullable=False)
  authorid = Column('authorid', Integer, ForeignKey('author.id'))
  children = relationship("Author",  lazy="select")


  def __init__(self, *args, **kwargs):
    super(User, self).__init__(*args, **kwargs)

class Author(AlchemyRecord, Base):
  __tablename__ = 'author'

  id = Column(Integer, primary_key=True)
  name = Column(String, unique=True)
  personid = Column('personid', Integer, ForeignKey('persons.id'))
  children = relationship("Persons",  lazy="select")


class Persons(AlchemyRecord, Base):
  __tablename__ = 'persons'

  id = Column(Integer)
  name = Column(String, primary_key=True)


def buildTables(connection, session):
  meta = MetaData()
  Table(
      'alchemy_users', meta,
      Column('id', Integer, primary_key=True),
      Column('username', String(255), nullable=False, unique=True),
      Column('password', String(255), nullable=False),
      Column('authorid', Integer, ForeignKey('author.id')),
    )
  Table(
    'author', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(32), nullable=False),
    Column('personid', Integer, ForeignKey('persons.id'))
  )
  Table(
    'persons', meta,
    Column('id', Integer,primary_key=True),
    Column('name', String(32), nullable=False)
  )

  meta.create_all(connection)

  Persons.Create(session, {'name': 'Person name'})
  Author.Create(session, {'name': 'Author name', 'personid': 1})
  Author.Create(session, {'name': 'Author number 2', 'personid': 1})
  User.Create(session, {'username': 'name', 'password': 'test', 'authorid': 1})


class UserPageMaker(SqAlchemyPageMaker):
  """Holds all the request handlers for the application"""

  def Sqlalchemy(self):
    """Returns the index template"""
    tables = inspect(self.engine).get_table_names()
    if not 'alchemy_users' in tables or not 'author' in tables or not 'persons' in tables:
      buildTables(self.engine, self.session)

    user = User.FromPrimary(self.session, 1)
    # print(User.Create(self.session, {'username': 'hello', 'password': 'test', 'authorid': 1}))
    # print("Returns user with primary key 1: ", user)
    # print("Will only load the children when we ask for them: ", user.children)
    # print("Conditional list, lists users with id < 10: ", list(User.List(self.session, conditions=[User.id <= 10])))
    print("List item 0: ",  list(User.List(self.session, conditions=[User.id <= 10]))[0])
    # print("List item 0.children: ",  list(User.List(self.session, conditions=[User.id <= 10]))[0].children)

    # User.Update(self.session, [User.id > 2, User.id < 100], {User.username: 'username', User.password: 'password'})
    # print("User from primary key", user)
    # user.Delete()
    # print(user.children)
    # print("deleted", User.DeletePrimary(self.session, user.key))
    # print(User.List(self.session, conditions=[User.id >= 1, User.id <= 10]))
    # print(user)
    # print("FromPrimary: ", user)
    # print(self.session.query(Persons, Author).join(Author).filter().all())
    # user.username = f'USERNAME{result.id}'
    # user.Save()
    # user.author.name = f'AUTHOR{result.id}'
    # user.author.Save()
    # print("EditedUser", user)
    # user_list = list(User.List(self.session, order=(User.id.desc(), User.username.asc())))
    # print("DeletePrimary: ", User.DeletePrimary(self.session, result.id))
    # print('---------------------------------------------------------------------------')
    return self.parser.Parse('sqlalchemy.html')
