#!/usr/bin/python
"""Request handlers for the uWeb3 project scaffold"""

from uweb3 import response
from uweb3.model import SettingsManager
from uweb3 import DebuggingPageMaker

class PageMaker(DebuggingPageMaker):
  """Holds all the request handlers for the application"""

  def Index(self):
    """Returns the index template"""
    return self.parser.Parse('index.html')

  def TestRoute(self):
    """Returns the index template"""
    return self.parser.Parse('index.html')

  def FourOhFour(self, path):
    """The request could not be fulfilled, this returns a 404."""
    self.req.response.httpcode = 404
    return self.parser.Parse('404.html', path=path)
