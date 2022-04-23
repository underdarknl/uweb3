#!/usr/bin/python3
"""This file contains the connector for Mysql."""
__author__ = 'Jan Klopper (janunderdark.nl)'
__version__ = 0.1

from . import Connector

class Mysql(Connector):
  """Adds MySQL support to connection manager object."""

  def __init__(self, config, options, request, debug=False):
    """Returns a MySQL database connection."""
    self.debug = debug
    self.options = {'host': 'localhost',
                   'user': None,
                   'password': None,
                   'database': ''}
    try:
      from ..libs.sqltalk import mysql
      try:
        self.options = options[self.Name()]
      except KeyError:
        pass
      # SSL support for mysql
      ssl = self.SSLConfig()
      self.connection = mysql.Connect(
        host=self.options.get('host', 'localhost'),
        user=self.options.get('user'),
        passwd=self.options.get('password'),
        db=self.options.get('database'),
        charset=self.options.get('charset', 'utf8'),
        ssl=ssl,
        debug=self.debug)
    except Exception as e:
      raise ConnectionError('Connection to "%s" of type "%s" resulted in: %r' % (self.Name(), type(self), e))

  def SSLConfig(self):
    ssl = None
    if any((self.options.get('ssl_ca'),
            self.options.get('ssl_key'),
            self.options.get('ssl_cert'))):
      ssl = {'ca': self.options.get('ssl_ca'),
             'capath': self.options.get('ssl_capath'),
             'check_hostname': self.options.get('ssl_check_hostname')}
      if 'ssl_cipher' in self.options:
        ssl['cipher'] = self.options.get('ssl_cipher')
      if 'ssl_cert' in self.options:
        ssl['key'] = self.options.get('ssl_key'),
        ssl['cert'] = self.options.get('ssl_cert')
    return ssl

  def Rollback(self):
    if self.debug:
      print('Rolling back uncommited transaction on Mysql connector')

    with self.connection as cursor:
      return cursor.Execute("ROLLBACK")

  def Disconnect(self):
    """Closes the MySQL connection."""
    if self.debug:
      print('%s closed connection to: %r' % (self.Name(), self.options.get('database')))
    self.connection.close()
    del(self.connection)
