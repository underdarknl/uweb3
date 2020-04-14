#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
import json
from uweb3 import PageMaker
from uweb3.pagemaker.new_login import UserCookie
from uweb3.pagemaker.new_decorators import loggedin, checkxsrf
from uweb3.ext_lib.underdark.libs.safestring import SQLSAFE, HTMLsafestring
from uweb3.model import SettingsManager

class Test(PageMaker):
  """Holds all the request handlers for the application"""
  
  @staticmethod
  def Limit(length=80):
    """Returns a closure that limits input to a number of chars/elements.""" 
    return lambda string: string[:length]

  def Test(self):
    """Returns the index template"""
    self.parser.RegisterFunction('substr', self.Limit)
    return self.parser.Parse('test.html', variable='test')
  
  def GetRawTemplate(self):
    """Endpoint that only returns the raw template"""
    template = self.get.getfirst('template')
    content_hash = self.get.getfirst('content_hash')
    if not template or not content_hash:
      return 404 
    del self.get['template']
    del self.get['content_hash']  
    kwds = {}
    for item in self.get:
      kwds[item] = self.get.getfirst(item)
    content = self.parser.Parse(template, returnRawTemplate=True, **kwds)
    if content.content_hash == content_hash:
      return content
    return 404

  def Parsed(self):
    self.parser.RegisterFunction('substr', self.Limit)
    kwds = {}
    template = self.get.getfirst('template')
    del self.get['template']
    for item in self.get:
      kwds[item] = self.get.getfirst(item)
    try:
      self.parser.noparse = True
      content = self.parser.Parse(
          template, **kwds)
    finally:
      self.parser.noparse = False
    return json.dumps(((self.req.headers.get('http_x_requested_with', None), self.parser.noparse, content)))

  def StringEscaping(self):
    if self.post:
      result = SQLSAFE(self.post.getfirst('sql'), self.post.getfirst('value1'), self.post.getfirst('value2'), unsafe=True)
      t = f"""t = 't"''"""
      print(result + t)
    return self.req.Redirect('/test')