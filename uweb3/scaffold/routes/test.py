#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker
from uweb3.pagemaker.new_decorators import loggedin, checkxsrf

class Test(PageMaker):
  """Holds all the request handlers for the application"""
  
  # @loggedin
  # @checkxsrf
  def Test(self):
    """Returns the index template"""
    return self.parser.Parse('test.html')
