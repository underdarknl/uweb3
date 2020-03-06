#!/usr/bin/python
"""uWeb3 model base classes."""

# Standard modules
import os
import datetime
import simplejson
import sys
import hashlib
import pickle
import secrets
import configparser

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect
from contextlib import contextmanager

class Error(Exception):
  """Superclass used for inheritance and external exception handling."""


class DatabaseError(Error):
  """Superclass for errors returned by the database backend."""


class BadFieldError(DatabaseError):
  """A field in the record could not be written to the database."""

class AlreadyExistError(Error):
  """The resource already exists, and cannot be created twice."""


class NotExistError(Error):
  """The requested or provided resource doesn't exist or isn't accessible."""


class PermissionError(Error):
  """The entity has insufficient rights to access the resource."""

class SettingsManager(object):
  def __init__(self):
    """Creates a ini file with the childs class name"""
    self.options = None
    self.FILENAME = "{}.ini".format(self.__class__.__name__)
    self.FILE_LOCATION = os.path.join(os.getcwd(), "base", self.FILENAME)
    if not os.path.isfile(self.FILE_LOCATION):
      os.mknod(self.FILE_LOCATION)
    self.config = configparser.ConfigParser()
    self.Read()
    
  def Create(self, section, key, value):
    """Creates a section or/and key = value
    
    Arguments:
      @ section: str
        Name of the section you want to create or append key = value to
      @ key: str
        Name of the key you want to create
      @ value: str
      
    Raises:
      ValueError
    """
    if not self.options.get(section):
      self.config.add_section(section)
    else:
      if self.config[section].get(key):
        raise ValueError("key already exists")
        
    self.config.set(section, key, value)
    
    with open(self.FILE_LOCATION, 'w') as configfile:
      self.config.write(configfile)
    self.Read()
    
  def Read(self):
    self.config.read(self.FILE_LOCATION)
    self.options = self.config._sections
  
  def Update(self, section, key, value):
    """Updates ini file
    After update reads file again and updates options attribute
    
    Arguments:
      @ section: str
      @ key: str
      @ value: str
      
    Raises
      TypeError: Option values must be string
    """
    if not self.options.get(section):
      self.config.add_section(section)
    self.config.set(section, key, value)
    
    with open(self.FILE_LOCATION, 'w') as configfile:
      self.config.write(configfile)
    self.Read()
  
  def Delete(self, section, key, delete_section=False):
    """Delete sections/keys from the INI file
    Be aware, deleting a section that is not empty will remove all keys from that
    given section
    
    Arguments:
      @ section: str
        Name of the section
      @ key: str
        Name of the key you want to remove
      % delete_section: boolean
        If set to true it will delete the supplied section
    Raises:
      configparser.NoSectionError
    """
    self.config.remove_option(section, key)
    if delete_section:
      self.config.remove_section(section)
    with open(self.FILE_LOCATION, 'w') as configfile:
      self.config.write(configfile)
    self.Read()
    
class SecureCookie(object):
  """ """
  #TODO: ini class in the model which makes a file based on the class name with
  #settings in it 
  
  def __init__(self, connection):
    self.req = connection[0]
    self.cookies = connection[1]
    self.cookie_salt = connection[2]
    self.cookiejar = self.__GetSessionCookies()

  def __GetSessionCookies(self):
    cookiejar = {}
    for key, value in self.cookies.items():
      isValid, value = self.__ValidateCookieHash(value)
      if isValid:
        cookiejar[key] = value
    return cookiejar
  
  def Create(self, name, data, **attrs):
    """Creates a secure cookie
    
    Arguments:
      @ name: str
        Name of the cookie
      @ data: dict 
        Needs to have a key called __name with value of how you want to name the 'table'
      % only_return_hash: boolean
        If this is set it will just return the hash of the cookie. This is used to 
        validate the cookies hash 
      % update: boolean
        Used to update the cookie. Updating actually means deleting and setting a new 
        one. This attribute is used by the update method from this class
      % expires: str ~~ None
        The date + time when the cookie should expire. The format should be:
        "Wdy, DD-Mon-YYYY HH:MM:SS GMT" and the time specified in UTC.
        The default means the cookie never expires.
        N.B. Specifying both this and `max_age` leads to undefined behavior.
      % path: str ~~ '/'
        The path for which this cookie is valid. This default ('/') is different
        from the rule stated on Wikipedia: "If not specified, they default to
        the domain and path of the object that was requested".
      % domain: str ~~ None
        The domain for which the cookie is valid. The default is that of the
        requested domain.
      % max_age: int
        The number of seconds this cookie should be used for. After this period,
        the cookie should be deleted by the client.
        N.B. Specifying both this and `expires` leads to undefined behavior.
      % secure: boolean
        When True, the cookie is only used on https connections.
      % httponly: boolean
        When True, the cookie is only used for http(s) requests, and is not
        accessible through Javascript (DOM).
        
    Raises:
      ValueError: When cookie with name already exists
    """ 
    if not attrs.get('update') and self.cookiejar.get(name):
      raise ValueError("Cookie with name already exists")
    if attrs.get('update'):
      self.cookiejar[name] = data
    
    hashed = self.__CreateCookieHash(data)
    if not attrs.get('only_return_hash'):
      #Delete all these settings to prevent them from injecting in a cookie
      if attrs.get('update'):
          del attrs['update']
      if attrs.get('only_return_hash'):
        del attrs['only_return_hash']
      self.req.AddCookie(name, hashed, **attrs)
    else:
      return hashed
    
  def Update(self, name, data, **attrs):
    """"Updates a secure cookie
    Keep in mind that the actual cookie is updated on the next request. After calling
    this method it will update the session attribute to the new value however.
    
    Arguments:
      @ name: str
        Name of the cookie
      @ data: dict 
        Needs to have a key called __name with value of how you want to name the 'table'
      % only_return_hash: boolean
        If this is set it will just return the hash of the cookie. This is used to 
        validate the cookies hash 
      % update: boolean
        Used to update the cookie. Updating actually means deleting and setting a new 
        one. This attribute is used by the update method from this class
      % expires: str ~~ None
        The date + time when the cookie should expire. The format should be:
        "Wdy, DD-Mon-YYYY HH:MM:SS GMT" and the time specified in UTC.
        The default means the cookie never expires.
        N.B. Specifying both this and `max_age` leads to undefined behavior.
      % path: str ~~ '/'
        The path for which this cookie is valid. This default ('/') is different
        from the rule stated on Wikipedia: "If not specified, they default to
        the domain and path of the object that was requested".
      % domain: str ~~ None
        The domain for which the cookie is valid. The default is that of the
        requested domain.
      % max_age: int
        The number of seconds this cookie should be used for. After this period,
        the cookie should be deleted by the client.
        N.B. Specifying both this and `expires` leads to undefined behavior.
      % secure: boolean
        When True, the cookie is only used on https connections.
      % httponly: boolean
        When True, the cookie is only used for http(s) requests, and is not
        accessible through Javascript (DOM).
        
    Raises:
      ValueError: When no cookie with given name found
    """
    if not self.cookiejar.get(name):
      raise ValueError("No cookie with name `{}` found".format(name))
    
    attrs['update'] = True
    self.Create(name, data, **attrs)
    
    
  def Delete(self, name):
    """Deletes cookie based on name
    The cookie is no longer in the session after calling this method
    
    Arguments:
      % name: str
        Deletes cookie by name
    """
    self.req.DeleteCookie(name)
    if self.cookiejar.get(name):
      self.cookiejar.pop(name)

        
  def __CreateCookieHash(self, data):
    hex_string = pickle.dumps(data).hex()
      
    hashed = (hex_string + self.cookie_salt).encode('utf-8')
    h = hashlib.new('ripemd160')
    h.update(hashed)
    return '{}+{}'.format(h.hexdigest(), hex_string)
  
  def __ValidateCookieHash(self, cookie):
    """Takes a cookie and validates it
    
    Arguments:
      @ str: A hashed cookie from the `__CreateCookieHash` method 
    """
    if not cookie:
      return None
    try:
      data = cookie.rsplit('+', 1)[1]
      data = pickle.loads(bytes.fromhex(data))
    except Exception:
      return (False, None)

    if cookie != self.__CreateCookieHash(data):
      return (False, None)
    
    return (True, data)



class BaseRecord(object):
  _record = {}
  key = None
  
  def __init__(self, session, record):
    """"""
    self.session = session
    self._BuildRecordClass(record)
  
  def _BuildRecordClass(self, record):
    if record:
      self._ValidateRecord(record, type(self))
      self.__dict__.update(record)
      self._record = dict(record)
      primary_key = inspect(type(self)).primary_key[0].name
      if primary_key in record:
        self.key = record[primary_key]
  
  def __repr__(self):
    return f'{type(self).__name__}({self._record})'
  
  def __len__(self):
    return len(self._record)
  
  def __eq__(self, other):
    if type(self) != type(other):
      return False  # Types must be the same.
    elif not (self.key == other.key is not None):
      return False  # Records should have the same non-None primary key value.
    elif len(self) != len(other):
      return False  # Records must contain the same number of objects.
    for key, value in self._record.items():
      other_value = other._record[key]
      if isinstance(self, BaseRecord) != isinstance(other, BaseRecord):
        # Only one of the two is a BaseRecord instance
        if (isinstance(self, BaseRecord) and value.key != other_value or
            isinstance(other, BaseRecord) and other_value.key != value):
          return False
      elif value != other_value:
        return False
    return True
  
  @classmethod
  def TableName(cls):
    """Returns the database table name for the Record class."""
    return cls.__tablename__

  @classmethod
  def _ValidateRecord(self, record, record_type):
    for item in record:
      if not item in (inspect(record_type).attrs):
        raise AttributeError(f'{item} not a valid column in {record_type}')
  
  @classmethod
  @contextmanager
  def session_scope(cls, Session):
    """Provide a transactional scope around a series of operations."""
    session = Session(expire_on_commit=False)
    try:
      yield session
      session.commit()
    except:
      session.rollback()
      raise
    finally:
      session.close()
  
  @classmethod    
  def _PrimaryKeyCondition(cls, target):
    return getattr(cls, inspect(cls).primary_key[0].name)

  @classmethod
  def _AlchemyRecordToDict(self, record):
    """This is needed because for some reason SQLalchemy makes a class of record it 
    returns from the database. However that record does not follow the init process
    and for that reason when we try and print it it will show Cls(None)
    """
    if not isinstance(record, type(None)):
      return dict((col, getattr(record, col)) for col in record.__table__.columns.keys())
    return None
  
class Record(BaseRecord):
  """ """
  
  @classmethod
  def Create(cls, session, record):
    """Creates a new record of the class. 
    
    Keep in mind that it will only insert the fields that are specified in the child
    that is inheriting from the Record/BaseRecord class.
    
    Arguments: 
      @ Session: sqlalchemy session object
        Available in the pagemaker with self.session
      @ Record: dictionary with matching SQL attributes of the class
      
    Raises:
      Sqlalchemy.exc
      
    Returns:
      Class: returns record inside a usable class object depending on the class that
      it was called with
    """
    #Create a new instance of the class that needs to be inserted into the database
    record = cls(session, record)
    #Set record values to the class. 
    with cls.session_scope(session) as current_session:
      current_session.add(record)
      current_session.commit()
    return cls(session, cls._AlchemyRecordToDict(record))
    
  @classmethod
  def FromPrimary(cls, session, p_key):
    """Finds record based on given class and supplied primary key
    
    Arguments:
      @ Session: sqlalchemy session object
        Available in the pagemaker with self.session
      @ P_key: integer
        primary_key of the object to delete
    """
    record = None
    with cls.session_scope(session) as current_session:
      record = current_session.query(cls).filter(
        cls._PrimaryKeyCondition(cls) == p_key).first()
      
    result = cls(session, cls._AlchemyRecordToDict(record))
    if not len(result):
      raise NotExistError(f"Record with primary key {p_key} does not exist")
    return cls(session, cls._AlchemyRecordToDict(record))
  
  def _Changes(self, new_record):
    """Returns the differences of the current state vs the last stored state."""
    sql_record = self._record
    changes = {}
    for key, value in sql_record.items():
      if new_record.get(key) != value:
        changes[key] = new_record.get(key)
    return changes
  
  def _SaveSelf(self):
    new_record = {}
    for item in inspect(type(self)).attrs:
      new_record[item.key] = getattr(self, item.key)
    difference = self._Changes(new_record)
    if difference:
      return self._Update(difference)
  
  def Save(self, save_foreign=False):
    """When changes are made to the class save them to the database and rebuild the 
    current record object
    """
    if save_foreign:
      return NotImplemented
    result = self._SaveSelf()
    if result:
      self._BuildRecordClass(result._record)
    
  def _Update(self, difference):
    """Update the object and return the new record class"""
    with self.session_scope(self.session) as current_session:
      record = current_session.query(type(self)).filter(
        self._PrimaryKeyCondition(type(self)) == self.key).first()
      for key, value in difference.items():
        setattr(record, key, value)
      return type(self)(self.session, self._AlchemyRecordToDict(record))
    
  @classmethod
  def DeletePrimary(cls, session, p_key):
    """Deletes the record of given class based on the supplied primary key
    
    Keep in mind that the primary key will only be found if it is specified in the child
    class. If for some reason multiple records match the criteria(shouldn't happen) 
    only the first record will be deleted
    
    Arguments:
      @ Session: sqlalchemy session object
        Available in the pagemaker with self.session
      @ P_key: integer
        primary_key of the object to delete
    """
    with cls.session_scope(session) as current_session:
      record = current_session.query(cls).filter(
        cls._PrimaryKeyCondition(cls) == p_key).first()
      current_session.delete(record)
      return cls(session, cls._AlchemyRecordToDict(record))
    
    
  @classmethod
  def List(cls, session, conditions=None, limit=None, offset=None,
           order=None, yield_unlimited_total_first=False):
    """Yields a Record object for every table entry.

    Arguments:
      @ connection: object
        Database connection to use.
      % conditions: list[{'column': 'value', 'operator': 'operator'|}]
        Optional query portion that will be used to limit the list of results.
        If multiple conditions are provided, they are joined on an 'AND' string.
        Operators are: <=, <, ==, >, >=, !=. Defaults to == if no operator is supplied 
      % limit: int ~~ None
        Specifies a maximum number of items to be yielded. The limit happens on
        the database side, limiting the query results.
      % offset: int ~~ None
        Specifies the offset at which the yielded items should start. Combined
        with limit this enables proper pagination.
      % order: tuple of operants
        For example the User class has 3 fields; id, username, password. We can pass
        the field we want to order on to the tuple like so; 
        (User.id.asc(), User.username.desc())
      % yield_unlimited_total_first: bool ~~ False
        Instead of yielding only Record objects, the first item returned is the
        number of results from the query if it had been executed without limit.
        
    Returns: int with length of results.
    Yields: Classes of requested query.
    """
    import operator
    ops = { 
           "<": operator.lt, 
           "<=": operator.le, 
           ">": operator.gt, 
           ">=": operator.ge, 
           "!=": operator.ne, 
           "==": operator.eq
           } 
    with cls.session_scope(session) as current_session:
      query = current_session.query(cls)
      if conditions:
        for item in conditions:
          attr = next(iter(item))
          value = item[next(iter(item))]
          operator = item.get('operator', '==')
          query = query.filter(ops[operator](getattr(cls, attr), value))
      if order:
        for item in order:
          query = query.order_by(item)
      if limit:
        query = query.limit(limit)
      if offset:
        query = query.offset(offset)
      result = query.all()  
      if yield_unlimited_total_first:
        return len(result)
      
      for record in result:
        yield cls(session, cls._AlchemyRecordToDict(record))
      