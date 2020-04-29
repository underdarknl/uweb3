#!/usr/bin/python3
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3 import PageMaker

class SocketHandler(PageMaker):
  """Holds all the request handlers for the application"""

  def EventHandler(sid, msg):
    # print(sid, msg)
    print("hello world from sockethandler")

  def Connect(sid, env):
    print(sid, env)