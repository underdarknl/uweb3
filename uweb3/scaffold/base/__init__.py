"""A minimal uWeb3 project scaffold."""

# Standard modules
import os

# Third-party modules
import uweb3

# Application
from . import pages


def main():
  """Creates a uWeb3 application.

  The application is created from the following components:

  - The presenter class (PageMaker) which implements the request handlers.
  - The routes iterable, where each 2-tuple defines a url-pattern and the
    name of a presenter method which should handle it.
  - The configuration file (ini format) from which settings should be read.
  """
  config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
  config = uweb3.read_config(config_file)
  routes = [
      ('/', 'Index'),
      ('/login', 'Login'),
      ('/home', 'Home'), 
      ('/home/create', 'Create'),
      ('/home/update', 'Update'),
      ('/home/delete', 'Delete'),
      ('/logout', 'Logout'),
      ('/sqlalchemy', 'Sqlalchemy'),
      #test routes
      ('/test', 'Test'),
      ('/getrawtemplate.*', 'GetRawTemplate'),
      ('/parsed', 'Parsed'),
      ('/test/escaping', 'StringEscaping'),
      ('/static/(.*)', 'Static'),
      ('/(.*)', 'FourOhFour'),
      ]
  
  return uweb3.uWeb(pages.PageMaker, routes, config=config)
