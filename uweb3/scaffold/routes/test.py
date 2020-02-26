#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import UserCookie
from uweb3.pagemaker.new_decorators import loggedin, checkxsrf

class Test(PageMaker):
  """Holds all the request handlers for the application"""
  
  @loggedin
  def Test(self):
    scookie = UserCookie(self.secure_cookie_connection)
    print(scookie.cookiejar)    
    """Returns the index template"""
    return self.parser.Parse('test.html')

  def Create(self):
    scookie = UserCookie(self.secure_cookie_connection)    
    scookie.Create("test", {"data": "somedata", "nested dict": {"data": "value"}})
    return self.req.Redirect('/test')

  
  def Update(self):
    scookie = UserCookie(self.secure_cookie_connection)
    scookie.Update("test", "replaced all data in the test cookie")
    return self.req.Redirect('/test')

    
  def Delete(self):
    scookie = UserCookie(self.secure_cookie_connection)
    scookie.Delete("test")
    return self.req.Redirect('/test')

    