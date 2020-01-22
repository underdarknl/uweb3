#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import User

class UserPageMaker(PageMaker):
  """Holds all the request handlers for the application"""

  def Login(self):
    """Returns the index template"""
    # print(self.connection)
    if self.req.method == 'POST':
  
      # try:
      #   User(self.post.form['username'], self.post.form['password'])
      # except Exception as e:
      #   print(e)
    # user = User()
    # print(user.FromName(self.connection, 'stef'))
    return self.parser.Parse('login.html')
