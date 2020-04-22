"""Starts a simple application development server."""

# Application
import os
import base
import sys
import socketio
import eventlet
from uweb3.helpers import StaticMiddleware
from uweb3.sockets import Uweb3SocketIO

def websocket_routes(sio):
  @sio.on("test")
  def test(id, msg):
    print("WEBSOCKET ROUTE CALLED: ", id, msg)

def main():
  sio = socketio.Server()
  websocket_routes(sio)
  return sio

if __name__ == '__main__':
  sio = main()
  Uweb3SocketIO(base.main(), sio)