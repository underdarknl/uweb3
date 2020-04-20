#!/usr/bin/python
"""uWeb3 Framework"""

__version__ = '0.4.4-dev'

# Standard modules
try:
  import ConfigParser as configparser
except ImportError:
  import configparser
import logging
import os
import re
import sys
import time
import threading
from wsgiref.simple_server import make_server


# Add the ext_lib directory to the path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'ext_lib')))

# Package modules
from . import pagemaker
from . import request

# Package classes
from .response import Response
from .response import Redirect
from .pagemaker import PageMaker
from .pagemaker import DebuggingPageMaker
from .pagemaker import SqAlchemyPageMaker
from .helpers import StaticMiddleware
from uweb3.model import SettingsManager
class Error(Exception):
  """Superclass used for inheritance and external excepion handling."""


class ImmediateResponse(Exception):
  """Used to trigger an immediate repsonse, foregoing the regular returns."""


class NoRouteError(Error):
  """The server does not know how to route this request"""


class Registry(object):
  """Something to hook stuff to"""
  
def TEST(*args, **kwds):
  print('hello world', args, kwds)

class uWeb(object):
  """Returns a configured closure for handling page requests.

  This closure is configured with a precomputed set of routes and handlers using
  the Router function. After this, incoming requests are processed and delegated
  to the correct PageMaker handler.

  The url in the received `req` object is taken and matches against the
  `router`` (refer to Router() for more documentation on this).


  Takes:
    @ page_class: PageMaker
      Class that holds request handling methods as defined in the `routes`
    @ router: request router
      The result of the Router() function.
    @ config: dict
      Configuration for the PageMaker. Typically contains entries for database
      connections, default search paths etc.

  Returns:
    RequestHandler: Configured closure that is ready to process requests.
  """
  def __init__(self, page_class, routes, config):
    self.page_class = page_class
    self.registry = Registry()
    self.registry.logger = logging.getLogger('root')
    self.router = router(routes)
    self.config = SettingsManager(filename='config')
    self.secure_cookie_secret = str(os.urandom(32))
    self.setup_routing()
    
  def __call__(self, env, start_response):
    """WSGI request handler.
    Accpepts the WSGI `environment` dictionary and a function to start the
    response and returns a response iterator.
    """
    req = request.Request(env, self.registry)
    page_maker = self.page_class(req, config=self.config.options, secure_cookie_secret=self.secure_cookie_secret)
    response = self.get_response(page_maker,
        req.path,
        req.env['REQUEST_METHOD'],
        req.env['host'])
    if not isinstance(response, Response):
      req.response.text = response
      response = req.response
      
    if hasattr(page_maker, '_PostRequest'):
      response = page_maker._PostRequest(response)
      
    start_response(response.status, response.headerlist)
    yield response.content.encode(response.charset)
    
  def get_response(self, page_maker, path, method, host):
    try:
      # We're specifically calling _PostInit here as promised in documentation.
      # pylint: disable=W0212
      page_maker._PostInit()
      # pylint: enable=W0212
      method, args, hostargs = self.router(path, method, host)
      return getattr(page_maker, method)(*args)
    except pagemaker.ReloadModules as message:
      reload_message = reload(sys.modules[self.page_class.__module__])
      return Response(content='%s\n%s' % (message, reload_message))
    except ImmediateResponse as err:
      return err[0]
    except (NoRouteError, Exception):
      return page_maker.InternalServerError(*sys.exc_info())

  def serve(self, hot_reloading=True):
    """Sets up and starts WSGI development server for the current app."""
    host = self.config.options['development'].get('host', 'localhost')
    port = self.config.options['development'].get('port', 8001)

    static_directory = [os.path.join(sys.path[0], 'base/static')]
    app = StaticMiddleware(self, static_root='static', static_dirs=static_directory)
    server = make_server(host, int(port), app)

    print('Running µWeb3 server on http://{}:{}'.format(server.server_address[0],server.server_address[1]))
    try:
      #Needs to check == True. Without it will trigger even when false
      if self.config.options['development'].get('dev', False) == 'True':
        HotReload(self.config.options['development'].get('dev', 'False'))
      server.serve_forever()
    except:
      server.shutdown()

  def setup_routing(self):
    if isinstance(self.page_class, list):
      routes = []
      for route in self.page_class[1:]:
        routes.append(route)
      self.page_class[0].AddRoutes(tuple(routes))
      self.page_class = self.page_class[0]

    default_route = "routes"
    automatic_detection = True
    if self.config.options.get('routing'):
      default_route = self.config.options['routing'].get('default_routing', default_route)
      automatic_detection = self.config.options['routing'].get('disable_automatic_route_detection', 'False') != 'True'

    if automatic_detection:
      self.page_class.LoadModules(default_routes=default_route)

def read_config(config_file):
  """Parses the given `config_file` and returns it as a nested dictionary."""
  parser = configparser.SafeConfigParser()
  try:
    parser.read(config_file)
  except configparser.ParsingError:
    raise ValueError('Not a valid config file: %r.' % config_file)
  return dict((section, dict(parser.items(section)))
              for section in parser.sections())


def router(routes):
  """Returns the first request handler that matches the request URL.

  The `routes` argument is an iterable of 2-tuples, each of which contain a
  pattern (regex) and the name of the handler to use for matching requests.

  Before returning the closure, all regexen are compiled, and handler methods
  are retrieved from the provided `page_class`.

  Arguments:
    @ routes: iterable of 2-tuples.
      Each tuple is a pair of `pattern` and `handler`, both are strings.

  Returns:
    request_router: Configured closure that processes urls.
  """
  req_routes = []
  for pattern, *details in routes:
    req_routes.append((re.compile(pattern + '$', re.UNICODE),
                      details[0], #handler,
                      details[1] if len(details) > 1 else 'ALL', #request types
                      details[2] if len(details) > 2 else '*')) #host

  def request_router(url, method, host):
    """Returns the appropriate handler and arguments for the given `url`.

    The`url` is matched against the compiled patterns in the `req_routes`
    provided by the outer scope. Upon finding a pattern that matches, the
    match groups from the regex and the unbound handler method are returned.

    N.B. The rules are such that the first matching route will be used. There
    is no further concept of specificity. Routes should be written with this in
    mind.

    Arguments:
      @ url: str
        The URL requested by the client.
      @ method: str
        The http method requested by the client.
      @ host: str
        The http host header value requested by the client.

    Raises:
      NoRouteError: None of the patterns match the requested `url`.

    Returns:
      2-tuple: handler method (unbound), and tuple of pattern matches.
    """
    
    for pattern, handler, routemethod, hostpattern in req_routes:
      if routemethod != 'ALL':
        # clearly not the route we where looking for
        if isinstance(routemethod, tuple):
          if method not in routemethod:
            continue
        if method != routemethod:
          continue

      hostmatch = None
      if hostpattern != '*':
        # see if we can match this host and extact any info from it.
        hostmatch = re.compile(f"^{host}$").match(hostpattern)
        if not hostmatch:
          # clearly not the host we where looking for
          continue
        hostmatch = hostmatch.groups()
      match = pattern.match(url)
      if match:
        return handler, match.groups(), hostmatch
    raise NoRouteError(url +' cannot be handled')
  return request_router


class HotReload(object):
    def __init__(self, dev, interval=1):
      self.running = threading.Event()
      self.interval = interval
      self.path = os.getcwd()
      if dev:
        from pathlib import Path
        self.path = str(Path(self.path).parents[1])
      self.thread = threading.Thread(target=self.run, args=())
      self.thread.daemon = True
      self.thread.start()
                  
    def run(self):
      """ Method runs forever and watches all files in the project folder.
      
      Does not trigger a reload when the following files change:
      - .pyc
      - .ini
      - .md
      - .html

      Changes in the HTML are noticed by the TemplateParser,
      which then reloads the HTML file into the object and displays the updated version.  
      """
      self.WATCHED_FILES = self.getListOfFiles()[1]
      WATCHED_FILES_MTIMES = [(f, os.path.getmtime(f)) for f in self.WATCHED_FILES]
      
      while True:
        if len(self.WATCHED_FILES) != self.getListOfFiles()[0]:
          print('{color}New file added or deleted\x1b[0m \nRestarting µWeb3'.format(color='\x1b[7;30;41m'))
          self.restart()
        for f, mtime in WATCHED_FILES_MTIMES:
          if os.path.getmtime(f) != mtime:
            print('{color}Detected changes in {file}\x1b[0m \nRestarting µWeb3'.format(color='\x1b[7;30;41m', file=f))
            self.restart()
        time.sleep(self.interval)
          
    def getListOfFiles(self):
      """Returns all files inside the working directory of uweb3. 
      Also returns a count so that we can restart on file add/remove. 
      """
      watched_files = [__file__]
      for r, d, f in os.walk(self.path):
        for file in f:
          ext = os.path.splitext(file)[1]
          if ext not in (".pyc", '.ini', '.md', '.html',):
            watched_files.append(os.path.join(r, file))
      return (len(watched_files), watched_files)   
      
    def restart(self):
      """Restart uweb3 with all provided system arguments."""
      self.running.clear()
      os.execl(sys.executable, sys.executable, * sys.argv)   