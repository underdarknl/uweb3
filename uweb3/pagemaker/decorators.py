"""This file holds all the decorators we use in this project."""

import pickle
import time
from datetime import datetime

import pytz
import simplejson
import codecs
# import _mysql_exceptions
import uweb3
from uweb3 import model
from pymysql import err

def loggedin(f):
    """Decorator that checks if the user requesting the page is logged in."""
    def wrapper(*args, **kwargs):
      try:
        args[0].user = args[0]._CurrentUser()
      except (uweb3.model.NotExistError, args[0].NoSessionError):
        path = '/login'
        if args[0].req.env['PATH_INFO'].strip() != '':
          path = '%s/%s' % (path, args[0].req.env['PATH_INFO'].strip())
        return uweb.Redirect(path)
      return f(*args, **kwargs)
    return wrapper

def checkxsrf(f):
    """Decorator that checks the user's XSRF.

    The function will compare the XSRF in the user's cookie  and  in the
    (post) request.
    """
    def wrapper(*args, **kwargs):
      if args[0].incorrect_xsrf_token:
        args[0].post.list = []
        return args[0].XSRFInvalidToken(
            'Your XSRF token was incorrect, please try again.')
      return f(*args, **kwargs)
    return wrapper

def validapikey(f):
    """Decorator that checks if the user requesting the page is using a valid api key."""
    def wrapper(*args, **kwargs):
      if not args[0].apikey:
        return args[0].NoSessionError('Your API key was incorrect, please try again.')
      return f(*args, **kwargs)
    return wrapper

def Cached(maxage=None, verbose=False, handler=None, *t_args, **t_kwargs):
    """Decorator that wraps checks the cache table for a cached page.
    The function will see if we have a recent cached output for this call,
    or if one is being created as we speak.
    Use by adding the decorator module and flagging a pagemaker function with
    it.
    from pages import decorators
    @decorators.Cached(60)
    def mypage()
    Arguments:
      maxage: int(60), cache time in seconds.
      verbose: bool(false), insert html comment with cache information.
    """
    def cache_decorator(f):
      def wrapper(*args, **kwargs):
        create = False
        name = f.__name__
        modulename = f.__module__
        # model.CachedPage.Clean(args[0].connection, maxage)
        handler.Clean(args[0].connection, maxage)
        requesttime = time.time()
        time.clock()
        sleep = 0.3
        try:  # see if we have a cached version thats not too old
          data = handler.FromSignature(args[0].connection,
                                                maxage,
                                                name, modulename,
                                                simplejson.dumps(args[1:]),
                                                simplejson.dumps(kwargs))
          if verbose:
            data = '%s<!-- cached %ds ago -->' % (
                                               pickle.loads(codecs.decode(data['data'].encode(), "base64")),
                                               data['age'])
          else:
            data = pickle.loads(codecs.decode(data['data'].encode(), "base64"))
        except model.CurrentlyWorking:  # we dont have anything fresh enough, but someones working on it
          age = 0
          while age < maxage:  # as long as there's no output, we should try periodically until we have waited too long
            time.sleep(sleep)
            age = (time.time() - requesttime)
            try:
              data = handler.FromSignature(args[0].connection,
                                                    maxage,
                                                    name, modulename,
                                                    simplejson.dumps(args[1:]),
                                                    simplejson.dumps(kwargs))
              break
            except Exception:
              sleep = min(sleep*2, 2)
          try:
            if verbose:
              data = '%s<!-- waited for fresh content for %s seconds -->' % (
                                               pickle.loads(codecs.decode(data['data'].encode(), "base64")),
                                               age)
            else:
              data = pickle.loads(codecs.decode(data['data'].encode(), "base64"))
          except NameError:
            create = True
        except uweb3.model.NotExistError:  # we don't have anything fresh enough, lets create
          create = True
        if create:
          try:
            cache = handler.Create(args[0].connection, {
              'name': name,
              'modulename': modulename,
              'args': simplejson.dumps(args[1:]),
              'kwargs': simplejson.dumps(kwargs),
              'creating': str(pytz.utc.localize(datetime.utcnow()))[0:19],
              'created': str(pytz.utc.localize(datetime.utcnow()))[0:19]
              })
            data = f(*args, **kwargs)
            cache['data'] = codecs.encode(pickle.dumps(data), "base64").decode()
            cache['created'] = str(pytz.utc.localize(datetime.utcnow()))[0:19]
            cache['creating'] = None
            cache.Save()
            if verbose:
              data = '%s<!-- Fresh -->' % data
          # except _mysql_exceptions.OperationalError:
          except Exception:
            pass
        return data
      return wrapper
    return cache_decorator

def TemplateParser(template, *t_args, **t_kwargs):
    """Decorator that wraps and returns the output.

    The output is wrapped in a templateparser call if its not already something
    that we prepared for direct output to the client.
    """
    def template_decorator(f):
      def wrapper(*args, **kwargs):
        pageresult = f(*args, **kwargs) or {}
        if not isinstance(pageresult, (str, uweb3.Response, uweb3.Redirect)):
          pageresult.update(args[0].CommonBlocks(*t_args, **t_kwargs))
          return args[0].parser.Parse(template, **pageresult)
        return pageresult
      return wrapper
    return template_decorator
