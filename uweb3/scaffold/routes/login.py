#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import Users

class UserPageMaker(PageMaker):
  """Holds all the request handlers for the application"""

  def Login(self):
    """Returns the index template"""
    if self.cookies.get('login'):
      if Users.validateCookie(self.cookies.get('login')).user_id:
        print("Validated user based on cookie")
    
    if self.req.method == 'POST':
      try:
        user = Users(self.post.form['username'], self.post.form['password'])
        if user == user.FromName(self.connection):
          print('login')
          self.req.AddCookie('login', user.cookie)
        else:
          print('Invalid username/password combination')
      except ValueError as e:
        print(e)

   
    return self.parser.Parse('login.html')
