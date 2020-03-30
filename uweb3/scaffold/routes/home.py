#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
import json
from uweb3 import PageMaker
from uweb3.pagemaker.new_decorators import loggedin
from uweb3.pagemaker.new_login import UserCookie


class Test(PageMaker):
  """Holds all the request handlers for the application"""
  @loggedin
  def Home(self):
    """Returns the index template"""
    return self.parser.Parse('home.html', variable='test')

  @loggedin
  def Create(self):
    scookie = UserCookie(self.secure_cookie_connection)    
    scookie.Create("test", {"data": "somedata", "nested dict": {"data": "value"}})
    return self.req.Redirect('/home')

  @loggedin
  def Update(self):
    scookie = UserCookie(self.secure_cookie_connection)
    scookie.Update("test", "replaced all data in the test cookie")
    return self.req.Redirect('/home')

  @loggedin
  def Delete(self):
    scookie = UserCookie(self.secure_cookie_connection)
    scookie.Delete("test")
    return self.req.Redirect('/home')