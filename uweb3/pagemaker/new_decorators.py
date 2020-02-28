import os
import time
import datetime
import hashlib

class XSRF(object):
  # secret = str(os.urandom(64))
  secret = "test"
  def __init__(self, req, post):
    """Checks if cookie with xsrf key is present. 
    
    If not generates xsrf token and places it in a cookie.
    Checks if xsrf token in post is equal to the one in the cookie and returns
    True when they do not match and False when they do match for the 'incorrect_xsrf_token' flag.
    """
    self.unix_timestamp = time.mktime(datetime.datetime.now().date().timetuple())
    self.req = req
    self.post = post
    
  def validate_token(self, userid):
    """Validate given xsrf token based on userid
    
    Arguments:
      @ userid: str/int
      
    Returns:
        IsValid: bool
    """ 
    token = self.Generate_xsrf_token(userid)
    #Check if the post request is not empty
    if self.post:
      #Check if the xsrf token is in the request and ensure that its valid
      if not self.post.get('xsrf'):
        return True
      if self.post.get('xsrf') != token:
        self.req.AddCookie('xsrf', token)
        return True
    else:
      return True
    return token != self.post.get('xsrf')

  def Generate_xsrf_token(self, userid):    
      hashed = (str(self.unix_timestamp) + self.secret + userid).encode('utf-8')
      h = hashlib.new('ripemd160')
      h.update(hashed)
      return h.hexdigest()

def loggedin(f):
    """Decorator that checks if the user requesting the page is logged in based on set cookie."""
    def wrapper(*args, **kwargs):
      if not args[0].user:
        return args[0].req.Redirect('/login')
      return f(*args, **kwargs)
    return wrapper

def checkxsrf(f):
    """Decorator that checks the user's XSRF.

    The function will compare the XSRF in the user's cookie  and  in the
    (post) request. Make sure to have xsrf_enabled = True in the config.ini
    """
    def wrapper(*args, **kwargs):
      xsrf = XSRF(args[0].req, args[0].post)
      if not args[0].cookies.get('xsrf'):
        if args[0].user:
          args[0].req.AddCookie('xsrf', xsrf.Generate_xsrf_token(args[0].user.get('user_id')))
      if args[0].req.method == "POST":
        post_xsrf_token = args[0].post.get('xsrf')
        if not post_xsrf_token:
          return args[0].XSRFInvalidToken(
                    'Your XSRF token was incorrect, please try again.'
                    )
        if args[0].options.get('security').get('xsrf_enabled'):
          isInvalid = xsrf.validate_token(args[0].user.get('user_id'))
          if isInvalid:
            return args[0].XSRFInvalidToken(
                    'Your XSRF token was incorrect, please try again.'
                    )
      return f(*args, **kwargs)
    return wrapper