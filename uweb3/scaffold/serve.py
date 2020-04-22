"""Starts a simple application development server."""

# Application
import base
import sys
import socketio
import eventlet
import os
from uweb3.helpers import StaticMiddleware

def main():
  sio = socketio.Server()
  app = base.main()
  app = socketio.WSGIApp(sio, app)
  static_directory = [os.path.join(sys.path[0], 'base/static')]
  app = StaticMiddleware(app, static_root='static', static_dirs=static_directory)
  
  @sio.event
  def connect(sid, environ):
    print('connect ', sid)

  return app

if __name__ == '__main__':
  app = main()
  eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 5000)), app)
