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
  
class UserPageMaker(SqAlchemyPageMaker):
  """Holds all the request handlers for the application"""
  
  def Login(self):
    """Returns the index template"""
    # buildTables(self.connection, self.session)
    # User.Update(self.session, [User.id > 2, User.id < 100], {User.username: 'username', User.password: 'password'})
    user = User.FromPrimary(self.session, 1)
    print("User from primary key", user)
    user.Delete()
    # print(user.children)
    # print("deleted", User.DeletePrimary(self.session, user.key))
    # print(User.List(self.session, conditions=[User.id >= 1, User.id <= 10]))
    # print(user)
    # print("FromPrimary: ", user)
    # # session.query(Persons, Author).join(Author).filter().all():
    # user.username = f'USERNAME{result.id}'
    # user.Save()
    # user.author.name = f'AUTHOR{result.id}'
    # user.author.Save()
    # print("EditedUser", user)
    # user_list = list(User.List(self.session, order=(User.id.desc(), User.username.asc())))
    # print("List item 0: ", user_list[0])
    # print("Conditional list: ", list(User.List(self.session, conditions=[User.id <= 10])))
    # print("DeletePrimary: ", User.DeletePrimary(self.session, result.id))
    # print('---------------------------------------------------------------------------')

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