class Event(object):
  def __init__(self):
    self.handlers = {}
  
  def __call__(self, event_name, *args, **kwds):
    """Handles calling functions that are listening to added events."""
    handlers = self.handlers.get(event_name)
    if not handlers:
      return
    for event_handler in handlers['handler']:
      event_handler(*args, **kwds)

  def add(self, event_name, handler):
    """Add a function to the Event class. 

    Arguments:
      @ event_name: str
        Name of the event. This is used to the functions that are attached to the event.
      @ handler: function
        The function that should be called when the supplied event_name is invoked. 
    """
    if not hasattr(handler, '__call__'):
      raise TypeError("Supplied handler must be a function") 

    if not self.handlers.get(event_name):
      self.handlers[event_name] = { "handler": [handler] }
    else:
      self.handlers.get(event_name)['handler'].append(handler)
  
  def remove(self, event_name, handler):
    """Remove a function from the event listener.
    
    Arguments:
      @ event_name: str
        Name of the event. This is used to the functions that are attached to the event.
      @ handler: str
        Name of the function that should be removed. 
        Removes all functions if they are attached to an event multiple times. 
    """
    event = self.handlers.get(event_name)
    if not event:
      return
    self.handlers[event_name] = event['handler'][:] = [item for item in event['handler'] if not item.__name__ == handler]
  
def init():
  global event_listener
  event_listener = Event()