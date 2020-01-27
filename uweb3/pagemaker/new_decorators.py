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
      if args[0].incorrect_xsrf_token:
        args[0].post.list = []
        return args[0].XSRFInvalidToken(
            'Your XSRF token was incorrect, please try again.')
      return f(*args, **kwargs)
    return wrapper