#!/usr/bin/python
"""Request handlers for the uWeb3 project scaffold"""

import uweb3
from uweb3.model import SettingsManager

from uweb3 import response
import os

class PageMaker(uweb3.DebuggingPageMaker):
  """Holds all the request handlers for the application"""

  def Index(self):
    """Returns the index template"""
    file = open('/home/stef/devel/uweb3/uweb3/scaffold/uweb3_template.zip', 'rb')
    fsize = os.path.getsize('/home/stef/devel/uweb3/uweb3/scaffold/uweb3_template.zip')
    res = response.Response(content=file, content_type="application/zip", headers={'Content-Disposition': 'attachment; filename=uweb3_template.zip', 'Content-Length': fsize})
    return res
    # return self.parser.Parse('index.html')

  def TestRoute(self):
    """Returns the index template"""
    return self.parser.Parse('index.html')

  def FourOhFour(self, path):
    """The request could not be fulfilled, this returns a 404."""
    self.req.response.httpcode = 404
    return self.parser.Parse('404.html', path=path)
