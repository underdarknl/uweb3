import os
import time
import datetime
import hashlib
from uweb3.request import PostDictionary

def loggedin(f):
    """Decorator that checks if the user requesting the page is logged in based on set cookie."""
    def wrapper(*args, **kwargs):
      if not args[0].user:
        return args[0].req.Redirect('/login', httpcode=303)
      return f(*args, **kwargs)
    return wrapper

def clear_form_data(*args):
  method = args[0].req.method.lower()
  #Set an attribute in the pagemaker that holds the form data on an invalid XSRF validation
  args[0].invalid_form_data = getattr(args[0], method)
  #Remove the form data from the PageMaker
  setattr(args[0], method, PostDictionary())
  #Remove the form data from the Request class
  args[0].req.vars[method] = PostDictionary()
  return args

def checkxsrf(f):
    """Decorator that checks the user's XSRF.

    The function will compare the XSRF in the user's cookie  and  in the
    (post) request. Make sure to have xsrf_enabled = True in the config.ini
    """
    def wrapper(*args, **kwargs):
      if args[0].req.method != "GET":
        if args[0].invalid_xsrf_token:
          args = clear_form_data(*args)
          return args[0].XSRFInvalidToken('XSRF token is invalid or missing')
      return f(*args, **kwargs)
    return wrapper

