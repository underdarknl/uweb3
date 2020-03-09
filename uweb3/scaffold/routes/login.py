#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import alchemy_model
from uweb3 import PageMaker, SqAlchemyPageMaker
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
  children = relationship("Author",  lazy="joined")
      
class Author(alchemy_model.Record, Base):
  __tablename__ = 'author'

  id = Column(Integer, primary_key=True)
  name = Column(String, unique=True)
  personid = Column('personid', Integer, ForeignKey('persons.id'))
  children = relationship("Persons",  lazy="joined")
  # test = Column(Integer)
  
  
class Persons(alchemy_model.Record, Base):
  __tablename__ = 'persons'
  
  id = Column(Integer)
  name = Column(String, primary_key=True)
         

def buildTables(connection):
  meta = MetaData()
  Table(
      'users', meta,
      Column('id', Integer, primary_key=True),
      Column('username', String(255), nullable=False),
      Column('password', String(255), nullable=False),
      Column('authorid', Integer, ForeignKey('author.id'))
    )
  Table(
    'author', meta, 
    Column('id', Integer,primary_key=True),
    Column('name', String(32), nullable=False),
    Column('personid', Integer, ForeignKey('persons.id'))
  )
  Table(
    'persons', meta,
    Column('id', Integer,primary_key=True),
    Column('name', String(32), nullable=False)
  )
  meta.create_all(connection)

class UserPageMaker(SqAlchemyPageMaker):
  """Holds all the request handlers for the application"""
  
  def Login(self):
    """Returns the index template"""
    # buildTables(self.connection)
    """Create column"""
    # result = User.Create(self.session, {'username': 'name', 'password': 'test', 'authorid': 1})
    # print(result)
    # print("Created: ", result)
    """Select FromPrimary"""
    # user = User.FromPrimary(self.session, 2)
    # session = self.session()
    """Join tables"""
    # session.query(Persons, Author).join(Author).filter().all():
    """Edit record"""
    # user.author.name = 'qwerty'
    # user.author.Save()
    #print(user)
    """Delete record"""
    # print("DeletePrimary: ", User.DeletePrimary(self.session, result.id))
    # print(user)
    """List with conditions"""
    print("List: ", list(User.List(self.session, order=(User.id.desc(), User.username.asc()))))
    # print("List: ", User.List(self.session, conditions=[{'id': '10', 'operator': '<='}]))

    return 200
    scookie = UserCookie(self.secure_cookie_connection)
    # test = Test()
    if self.req.method == 'POST':
      try:
        user = Users()
        # user = user.FromPrimary(self.connection, self.session, 1)
        if Users.ComparePassword(self.post.get('password'), user['password']):
          scookie.Create("login", {
                'user_id': user['id'],
                'premissions': 1,
                'data': {'data': 'data'}
                })
          return self.req.Redirect('/test')
        else:
          print('Wrong username/password combination')      
      except uweb3.model.NotExistError as e:
        print(e)
        
    return self.parser.Parse('login.html')

  @checkxsrf
  def Logout(self):
    scookie = UserCookie(self.secure_cookie_connection)
    scookie.Delete('login')
    return self.req.Redirect('/login')