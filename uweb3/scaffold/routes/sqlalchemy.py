#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

from uweb3 import SqAlchemyPageMaker
from uweb3.alchemy_model import AlchemyRecord
from uweb3.pagemaker.new_login import Users, UserCookie, Test
from uweb3.pagemaker.new_decorators import checkxsrf

from sqlalchemy import Column, Integer, String, update, MetaData, Table, ForeignKey, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, lazyload

Base = declarative_base()

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
