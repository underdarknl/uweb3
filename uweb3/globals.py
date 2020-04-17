class Event(object):
  def __init__(self):
    self.handlers = {}
  
  def add(self, event_name, handler):
    if not self.handlers.get(event_name):
      self.handlers[event_name] = { "handler": [handler] }
    else:
      self.handlers.get(event_name)['handler'].append(handler)
  
  def remove(self, handler, event_name):
    event = self.handlers.get(event_name)
    if not event:
      return
  
  def __call__(self, event_name, *args, **kwds):
    handlers = self.handlers.get(event_name)
    if not handlers:
      return
    for event_handler in handlers['handler']:
      event_handler(*args, **kwds)

def init():
  global event_listener
  event_listener = Event()