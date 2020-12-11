import os
import sys

import socketio
import eventlet

from uweb3 import uWeb, HotReload
from uweb3.helpers import StaticMiddleware


class SocketMiddleWare(socketio.WSGIApp):
  def __init__(self, socketio_server, uweb3_server, socketio_path='socket.io'):
    super(SocketMiddleWare, self).__init__(socketio_server,
                                           uweb3_server,
                                           socketio_path=socketio_path
                                           )

class Uweb3SocketIO:
  def __init__(self, app, sio, static_dir=os.path.dirname(os.path.abspath(__file__))):
    if not isinstance(app, uWeb):
      raise Exception("App must be an uWeb3 instance!")

    self.host = app.config.options['development'].get('host', '127.0.0.1')
    self.port = app.config.options['development'].get('port', 8000)
    if app.config.options['development'].get('dev', False) == 'True':
      HotReload(app.executing_path, uweb_dev=app.config.options['development'].get('uweb_dev', 'False'))
    self.setup_app(app, sio, static_dir)


  def setup_app(self, app, sio, static_dir):
    path = os.path.join(app.executing_path, 'static')
    app = SocketMiddleWare(sio, app)
    static_directory = [os.path.join(sys.path[0], path)]
    app = StaticMiddleware(app, static_root='static', static_dirs=static_directory)
    eventlet.wsgi.server(eventlet.listen((self.host, int(self.port))), app)
