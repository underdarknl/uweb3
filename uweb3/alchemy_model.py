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
  
  # def __repr__(self):
  #   return str(vars(self))
  
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
  def _ValidateRecord(cls, record, record_type):
    """Validate if all attributes are part of the class. This validation works based
    on how you defined the class with the sqlalchemy classes such as String, Integer.

    Raises: 
      AttributeError: if the item is not a valid column or child from the parent
    """
    for item in record:
      if not item in (inspect(record_type).attrs):
        if not issubclass(type(record[item]), BaseRecord):
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
  def _AlchemyRecordToDict(cls, record, session):
    """This is needed because for some reason SQLalchemy makes a class of record it 
    returns from the database. However that record does not follow the init process
    and for that reason when we try and print it it will show Cls(None)
    
    If a child class is present it will load it as the name of the childs class, if 
    the name of the child is already in the dictionary it will add a _ prefix. 
    """
    if not isinstance(record, type(None)):
      parent = dict((col, getattr(record, col)) for col in record.__table__.columns.keys())
      if hasattr(record, 'children'):
        if not isinstance(record.children, type(None)):
          res = type(record.children)(session, cls._AlchemyRecordToDict(record.children, session))
          child_name = res.__class__.__name__.lower()
          if not child_name in parent:
            parent[child_name] = res
          else:
            parent[f'_{child_name}'] = res
      return parent
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
    with cls.session_scope(session) as current_session:
      current_session.add(record)
    return cls.FromPrimary(session, 
                           getattr(record, cls._PrimaryKeyCondition(record).name))
    
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
    result = cls(session, cls._AlchemyRecordToDict(record, session))
    if not len(result):
      raise NotExistError(f"Record with primary key {p_key} does not exist")
    return result
  
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
      if isinstance(record, type(None)):
        raise NotExistError("Record no longer exists.")
      for key, value in difference.items():
        setattr(record, key, value)
      return type(self)(self.session, self._AlchemyRecordToDict(record, self.session))
    
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
      return cls(session, cls._AlchemyRecordToDict(record, session))
    
    
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
        yield cls(session, cls._AlchemyRecordToDict(record, session))
      