#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import alchemy_model
from uweb3 import SqAlchemyPageMaker, PageMaker
from uweb3.pagemaker.new_login import Users, UserCookie, Test
from uweb3.pagemaker.new_decorators import checkxsrf

from sqlalchemy import Column, Integer, String, update, MetaData, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, lazyload

Base = declarative_base()

class User(alchemy_model.Record, Base):
  __tablename__ = 'users'

  id = Column(Integer, primary_key=True)
  username = Column(String, nullable=False, unique=True)
  password = Column(String, nullable=False) 
  authorid = Column('authorid', Integer, ForeignKey('author.id'))
  children = relationship("Author",  lazy="select")
  
  
  def __init__(self, *args, **kwargs):
    super(User, self).__init__(*args, **kwargs)
      
class Author(alchemy_model.Record, Base):
  __tablename__ = 'author'

  id = Column(Integer, primary_key=True)
  name = Column(String, unique=True)
  personid = Column('personid', Integer, ForeignKey('persons.id'))
  children = relationship("Persons",  lazy="select")
  
  
class Persons(alchemy_model.Record, Base):
  __tablename__ = 'persons'
  
  id = Column(Integer)
  name = Column(String, primary_key=True)
         

def buildTables(connection, session):
  meta = MetaData()
  Table(
      'users', meta,
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
  
class UserPageMaker(PageMaker):
  """Holds all the request handlers for the application"""
  
  def Login(self):
    """Returns the index template"""
    scookie = UserCookie(self.secure_cookie_connection)
    if self.req.method == 'POST':
      try:
        if 'login' in scookie.cookiejar:
          return self.req.Redirect('/home')
        user = Users.FromName(self.connection, self.post.getfirst('username'))
        if Users.ComparePassword(self.post.getfirst('password'), user['password']):
          scookie.Create("login", {
                'user_id': user['id'],
                'premissions': 1,
                'data': {'data': 'data'}
                })
          return self.req.Redirect('/home')
        else:
          print('Wrong username/password combination')      
      except uweb3.model.NotExistError as e:
        Users.CreateNew(self.connection, { 'username': self.post.getfirst('username'), 'password' : self.post.getfirst('password')})
        print(e)
        
    return self.parser.Parse('login.html')

  @checkxsrf
  def Logout(self):
    scookie = UserCookie(self.secure_cookie_connection)
    scookie.Delete('login')
    return self.req.Redirect('/login')