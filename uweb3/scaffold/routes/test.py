#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import UserCookie
from uweb3.pagemaker.new_decorators import loggedin, checkxsrf
from uweb3.ext_lib.underdark.libs.safestring import SQLSAFE, HTMLsafestring


class Test(PageMaker):
  """Holds all the request handlers for the application"""
  
  # @loggedin
  def Test(self):
    """Returns the index template"""
    # print(type(HTMLsafestring("oi")))
    return self.parser.Parse('test.html', q=HTMLsafestring('test<b>hello</b>', unsafe=True))

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

  def StringEscaping(self):
    if self.post:
      result = SQLSAFE(self.post.getfirst('sql'), 
              self.post.getfirst('value1'), 
              self.post.getfirst('value2'), 
              kwd=self.post.getfirst('keyword') 
              )
      print(result)
      # print(SQLSAFE("INSERT INTO user (username, password) VALUES ('test', 'test')", unsafe=True))
    return self.req.Redirect('/test')