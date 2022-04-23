class Connection:
  def __init__(self, request, cookies, cookie_secret):
    self.request = request
    self.cookies = cookies
    self.cookie_secret = cookie_secret
    self.queries = []
