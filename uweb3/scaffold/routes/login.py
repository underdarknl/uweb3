#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import SqAlchemyPageMaker, PageMaker
from uweb3.pagemaker.new_login import Users, UserCookie, Test
from uweb3.pagemaker.new_decorators import checkxsrf

class UserPageMaker(PageMaker):
  """Holds all the request handlers for the application"""
  def __init__(self, *args, **kwds):
    super(UserPageMaker, self).__init__(*args, **kwds)
    
  def Login(self):
    """Returns the index template"""
    scookie = UserCookie(self.secure_cookie_connection)
    if self.req.method == 'POST':
      try:
        if 'login' in scookie.cookiejar:
          return self.req.Redirect('/home', http_code=303)
        user = Users.FromName(self.connection, self.post.getfirst('username'))
        if Users.ComparePassword(self.post.getfirst('password'), user['password']):
          scookie.Create("login", {
                'user_id': user['id'],
                'permissions': 1,
                'data': {'data': 'data'}
                })
          return self.req.Redirect('/home', http_code=303)
        else:
          print('Wrong username/password combination')      
      except uweb3.model.NotExistError as e:
        Users.CreateNew(self.connection, { 'username': self.post.getfirst('username'), 'password' : self.post.getfirst('password')})
        print(e)  
    return self.parser.Parse('login.html')