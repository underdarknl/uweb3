#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
# from uweb3.pagemaker.new_login import User

class User(PageMaker):
  """Holds all the request handlers for the application"""

  def Login(self):
    """Returns the index template"""
    # print(self.connection)
    return self.parser.Parse('login.html')
