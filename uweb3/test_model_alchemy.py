#!/usr/bin/python
"""Test suite for the database abstraction module (model)."""

# Too many public methods
# pylint: disable=R0904

# Standard modules
import unittest

# Custom modules
# import newweb
# Importing newWeb makes the SQLTalk library available as a side-effect
import uweb3
from uweb3.ext_lib.underdark.libs.sqltalk import mysql
# Unittest target
from uweb3 import alchemy_model as model
import pymysql
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager

# ##############################################################################
# Record classes for testing
#
Base = declarative_base()

class Author(uweb3.alchemy_model.Record, Base):
  __tablename__ = 'author'
  id = Column(Integer, primary_key=True)
  name = Column(String(32), nullable=False)

  def __repr__(self):
    return "<Author(ID='%s', name='%s')>" % (self.id, self.name)
  


class RecordTests(unittest.TestCase):
  """Online tests of methods and behavior of the Record class."""
  def setUp(self):
    """Sets up the tests for the Record class."""
    self.meta = MetaData()
    author = Table(
      'author', self.meta,
      Column('ID', Integer, primary_key=True),
      Column('name', String(32), nullable=False),
    )
    book = Table(
      'book', self.meta, 
      Column('ID', Integer,primary_key=True),
      Column('author', Integer, nullable=False),
      Column('title', String(32), nullable=False)
    )
    self.engine = DatabaseConnection()
    self.session = Create_session(self.engine)
    self.meta.create_all(self.engine)

  def tearDown(self):
    """Destroy tables after testing."""
    for tbl in reversed(self.meta.sorted_tables):
      tbl.drop(self.engine)

  def testLoadPrimary(self):
    """[Record] Records can be loaded by primary key using FromPrimary()"""
    author = Author.Create(self.session, {'name': 'A. Chrstie'})
    self.assertEqual(type(author), Author)
    print(author)
    # author = Author.FromPrimary(self.connection, inserted.insertid)
    # self.assertEqual(type(author), Author)
    # self.assertEqual(len(author), 2)
    # self.assertEqual(author.key, inserted.insertid)
    # self.assertEqual(author['name'], 'A. Chrstie')


def DatabaseConnection():
  """Returns an SQLTalk database connection to 'newweb_model_test'."""
  return create_engine('mysql://{user}:{passwd}@{host}/{db}'.format(
    host='localhost',
    user='stef',
    passwd='24192419',
    db='uweb_test'
  ))
  
def Create_session(engine):
  from sqlalchemy.orm import sessionmaker
  Session = sessionmaker(autocommit=False)
  Session.configure(bind=engine)
  return Session

if __name__ == '__main__':
  unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
