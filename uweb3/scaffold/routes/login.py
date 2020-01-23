#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import Users

class UserPageMaker(PageMaker):
  """Holds all the request handlers for the application"""

  def Login(self):
    """Returns the index template"""
    # if self.cookies.get('login'):
    #   if Users.validateCookie(self.cookies.get('login')).user_id:
    #     print("Validated user based on cookie")
    # print(Users.Create(self.connection, 'test', 'password'))
  
    if self.req.method == 'POST':
      try:
        user = Users.FromName(self.connection, self.post.form.get('username'))._record
        if Users.ComparePassword(self.post.form.get('password'), user['password']):
          print('login')
          cookie = Users.CreateValidationCookieHash(user['id'])
          print(Users.ValidateUserCookie(cookie))
        else:
          print('Wrong username/password combination')      
      except uweb3.model.NotExistError as e:
        print(e)

    return self.parser.Parse('login.html', year='test')
