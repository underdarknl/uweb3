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
from sqlalchemy.orm import sessionmaker, reconstructor
from sqlalchemy.orm.session import object_session
from sqlalchemy.inspection import inspect
from contextlib import contextmanager

from itertools import chain

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
  def __init__(self, session, record):
    self.session = session
    self._BuildClassFromRecord(record)
    
  def _BuildClassFromRecord(self, record):
    if isinstance(record, dict):
      for key, value in record.items():
        if not key in self.__table__.columns.keys():
          raise AttributeError(f"Key '{key}' not specified in class '{self.__class__.__name__}'")
        setattr(self, key, value)
      if self.session:
        self.session.add(self)
        self.session.commit()
    
  def __hash__(self):
    """Returns the hashed value of the key."""
    return hash(self.key)
                   
  def __repr__(self):
    s = {}
    for key in self.__table__.columns.keys():
      value = getattr(self, key)
      if value:
        s[key] = value
    return f'{type(self).__name__}({s})'
  
  def __eq__(self, other):
    if type(self) != type(other):
      return False  # Types must be the same.
    elif not (self.key == other.key is not None):
      return False  # Records should have the same non-None primary key value.
    elif len(self) != len(other):
      return False  # Records must contain the same number of objects.
    for key in self.__table__.columns.keys():
      value = getattr(self, key)
      other_value = getattr(other, key)
      if isinstance(self, BaseRecord) != isinstance(other, BaseRecord):
        # Only one of the two is a BaseRecord instance
        if (isinstance(self, BaseRecord) and value.key != other_value or
            isinstance(other, BaseRecord) and other_value.key != value):
          return False
      elif value != other_value:
        return False
    return True
  
  def __ne__(self, other):
    """Returns the proper inverse of __eq__."""
    # Without this, the non-equal checks used in __eq__ will not work,
    # and the  `!=` operator would not be the logical inverse of `==`.
    return not self == other
  
  def __len__(self):
    return len(dict((col, getattr(self, col)) for col in self.__table__.columns.keys() if getattr(self, col)))
    
  def __int__(self):
    """Returns the integer key value of the Record.

    For record objects where the primary key value is not (always) an integer,
    this function will raise an error in the situations where it is not.
    """
    key_val = self.key
    if not isinstance(key_val, (int)):
      # We should not truncate floating point numbers.
      # Nor turn strings of numbers into an integer.
      raise ValueError('The primary key is not an integral number.')
    return key_val
  
  def copy(self):
    """Returns a shallow copy of the Record that is a new functional Record."""
    import copy
    return copy.copy(self)
  
  def deepcopy(self):
    import copy
    return copy.deepcopy(self)
   
  def __gt__(self, other):
    """Index of this record is greater than the other record's.

    This requires both records to be of the same record class."""
    if type(self) == type(other):
      return self.key > other.key
    return NotImplemented

  def __ge__(self, other):
    """Index of this record is greater than, or equal to, the other record's.

    This requires both records to be of the same record class."""
    if type(self) == type(other):
      return self.key >= other.key
    return NotImplemented

  def __lt__(self, other):
    """Index of this record is smaller than the other record's.

    This requires both records to be of the same record class."""
    if type(self) == type(other):
      return self.key < other.key
    return NotImplemented

  def __le__(self, other):
    """Index of this record is smaller than, or equal to, the other record's.

    This requires both records to be of the same record class."""
    if type(self) == type(other):
      return self.key <= other.key
    return NotImplemented 
  
  def __getitem__(self, field):
    return getattr(self, field)
  
  def iteritems(self):
    """Yields all field+value pairs in the Record.

    N.B. This automatically resolves foreign references.
    """
    return chain(((key, getattr(self, key)) for key in self.__table__.columns.keys()),  
    ((child[0], getattr(self, child[0])) for child in inspect(type(self)).relationships.items()))

  def itervalues(self):
    """Yields all values in the Record, loading foreign references."""
    return chain((getattr(self, key) for key in self.__table__.columns.keys()), 
                 (getattr(self, child[0]) for child in inspect(type(self)).relationships.items()))

  def items(self):
    """Returns a list of field+value pairs in the Record.

    N.B. This automatically resolves foreign references.
    """
    return list(self.iteritems())

  def values(self):
    """Returns a list of values in the Record, loading foreign references."""
    return list(self.itervalues())
    
  @property
  def key(self):
    return getattr(self, inspect(type(self)).primary_key[0].name)
  
  @classmethod
  def TableName(cls):
    """Returns the database table name for the Record class."""
    return cls.__tablename__
  
  @classmethod
  def _AlchemyRecordToDict(cls, record):
    """This is needed because for some reason SQLalchemy makes a class of record it 
    returns from the database. However that record does not follow the init process
    and for that reason when we try and print it it will show Cls(None)
    
    If a child class is present it will load it as the name of the childs class, if 
    the name of the child is already in the dictionary it will add a _ prefix. 
    """
    if not isinstance(record, type(None)):
      return dict((col, getattr(record, col)) for col in record.__table__.columns.keys())
    return None
  
  @reconstructor
  def reconstruct(self):
    """This is called instead of __init__ when the result comes from the database"""
    self.session = object_session(self)
  
  @classmethod    
  def _PrimaryKeyCondition(cls, target):
    return getattr(cls, inspect(cls).primary_key[0].name)
    
class Record(BaseRecord):
  """ """
  @classmethod
  def FromPrimary(cls, session, p_key):
    """Finds record based on given class and supplied primary key.
    
    Arguments:
      @ Session: sqlalchemy session object
        Available in the pagemaker with self.session
      @ P_key: integer
        primary_key of the object to delete
    Returns
      BaseRecord
      None
    """
    record = session.query(cls).filter(cls._PrimaryKeyCondition(cls) == p_key).first()
    if not record:
      raise NotExistError(f"Record with primary key {p_key} does not exist")
    return record
  
  @classmethod
  def DeletePrimary(cls, session, p_key):
    """Deletes record base on primary key from given class.
    
    Arguments:
      @ Session: sqlalchemy session object
        Available in the pagemaker with self.session
      @ P_key: integer
        primary_key of the object to delete
        
    Returns:
      isdeleted: boolean
      True or False based on if a record was deleted or not    
    """
    isdeleted = session.query(cls).filter(cls._PrimaryKeyCondition(cls) == p_key).delete()
    session.commit()
    return isdeleted
   
  def Save(self):
    """Saves any changes made in the current record. Sqlalchemy automaticly detects 
    these changes and only updates the changed values. If no values are present
    no query will be commited."""
    self.session.commit()
    
  @classmethod  
  def Create(cls, session, record):
    return cls(session, record)
    
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
        
    Returns: 
      Length: integer with length of results.
      List: List of classes from request type
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
    query = session.query(cls)
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
    return result
  
     
