#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker

class SocketHandler(PageMaker):
  """Holds all the request handlers for the application"""
    
  def EventHandler(self):
    print("hello world!")

