#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
import json
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import UserCookie
from uweb3.pagemaker.new_decorators import loggedin, checkxsrf
from uweb3.ext_lib.underdark.libs.safestring import SQLSAFE, HTMLsafestring


class Test(PageMaker):
  """Holds all the request handlers for the application"""
  
  @staticmethod
  def Limit(length=80):
    """Returns a closure that limits input to a number of chars/elements.""" 
    return lambda string: string[:length]

  # @loggedin
  def Test(self):
    """Returns the index template"""
    self.parser.RegisterFunction('substr', self.Limit)
    return self.parser.Parse('test.html', variable='test')
  
  def GetRawTemplate(self):
    """Endpoint that only returns the raw template"""
    return self.parser.Parse('test.html', returnRawTemplate=True)

  def Parsed(self):
    self.parser.RegisterFunction('substr', self.Limit)
    kwds = {}
    for item in self.get:
      kwds[item] = self.get.getfirst(item)
    self.parser.noparse = True
    content = self.parser.Parse(
        'test.html', **kwds)
    self.parser.noparse = False
    print(content)
    return json.dumps(((self.req.headers.get('http_x_requested_with', None), self.parser.noparse, content)))
  
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
              self.post.getfirst('value1'))
      # print(SQLSAFE("INSERT INTO user (username, password) VALUES ('test', 'test')", unsafe=True))
    return self.req.Redirect('/test')