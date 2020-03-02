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

  def StringEscaping(self):
    if self.post:
      # SQLSAFE(self.post.getfirst('sql'), 
      #                      ('test', 'test',), 
      #                      kwd=self.post.getfirst('kwd'))
      # print(SQLSAFE("SELECT * FROM users where username={} and test=test and this is this".format('username')))
      sql = "SELECT * FROM users (id, username) VALUES ({}, {})".format(self.post.getfirst('value1'), str(self.post.getfirst('value2')))
      SQLSAFE(sql)
      # SQLSAFE("INSERT INTO users (username, password, test) VALUES ('test','test', 1)")
      
    return self.req.Redirect('/test')