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
      #TODO: How do we supply the seed for generating an XSRF token?
      #In this case we use the user_id but how do we get it
      args[0].user = {'user_id': '1'}

      xsrf_cookie = args[0].cookies.get('xsrf')
      xsrf = XSRF(args[0].req.AddCookie, args[0].post)
      if args[0].req.method == "GET":
        if not xsrf_cookie:
          #If the cookie doesn't exist generate a token and add it in a cookie
          args[0].xsrf = xsrf.Generate_xsrf_token(args[0].user.get('user_id'))
          args[0].req.AddCookie('xsrf', args[0].xsrf)
        else:
          #If the cookie exists but the xsrf is not valid replace the cookie with a valid one
          if not xsrf.is_valid_xsrf_token(args[0].user.get('user_id')):
            args[0].xsrf = xsrf.Generate_xsrf_token(args[0].user.get('user_id'))
            args[0].req.AddCookie('xsrf', args[0].xsrf)
          else:
            args[0].xsrf = xsrf_cookie
      else:
        #On a post request check if there is a cookie with xsrf and if the post contains an xsrf input
        if not xsrf_cookie:
          args = clear_form_data(*args)
          return args[0].XSRFInvalidToken('XSRF cookie is missing')
        if not args[0].post.get('xsrf'):
          args = clear_form_data(*args)
          return args[0].XSRFInvalidToken('XSRF token is missing')
        #Validate token
        if not xsrf.is_valid_xsrf_token(args[0].user.get('user_id')):
          args = clear_form_data(*args)
          return args[0].XSRFInvalidToken('XSRF token is not valid')
        args[0].xsrf = xsrf_cookie
      return f(*args, **kwargs)
    return wrapper


class XSRF(object):
  # secret = str(os.urandom(64))
  secret = "test"
  def __init__(self, AddCookie, post):
    """Checks if cookie with xsrf key is present.

    If not generates xsrf token and places it in a cookie.
    Checks if xsrf token in post is equal to the one in the cookie and returns
    True when they do not match and False when they do match for the 'incorrect_xsrf_token' flag.
    """
    self.unix_timestamp = time.mktime(datetime.datetime.now().date().timetuple())
    self.AddCookie = AddCookie
    self.post = post

  def is_valid_xsrf_token(self, userid):
    """Validate given xsrf token based on userid

    Arguments:
      @ userid: str/int

    Returns:
        IsValid: boolean
    """
    token = self.Generate_xsrf_token(userid)
    if not self.post.get('xsrf'):
      return False
    if self.post.get('xsrf') != token:
      return False
    return True

  def Generate_xsrf_token(self, userid):
      hashed = (str(self.unix_timestamp) + self.secret + userid).encode('utf-8')
      h = hashlib.new('ripemd160')
      h.update(hashed)
      return h.hexdigest()

