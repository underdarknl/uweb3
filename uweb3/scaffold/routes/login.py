#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import Users
from uweb3 import templateparser
from uweb3.response import Response

class UserPageMaker(PageMaker):
  """Holds all the request handlers for the application"""
  def Login(self):
    """Returns the index template"""
    if self.cookies.get('login'):
      if Users.ValidateUserCookie(self.cookies.get('login')):
        print("Validated user based on cookie")
        
    if self.req.method == 'POST':
      try:
        user = Users.FromName(self.connection, self.post.form.get('username'))._record
        if Users.ComparePassword(self.post.form.get('password'), user['password']):
          cookie = Users.CreateValidationCookieHash(user['id'])
          self.req.AddCookie('login', cookie)
          return self.req.Redirect('/test')
        else:
          print('Wrong username/password combination')      
      except uweb3.model.NotExistError as e:
        print(e)
    print('redirect')
    return self.parser.Parse('login.html', xsrf=11)
