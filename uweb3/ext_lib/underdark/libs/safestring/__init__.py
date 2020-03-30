#!/usr/bin/python3
"""This module contains a set of classes which can be used in a multi-facet
environment like a web-application to maintain knowledge about the origin of
strings. It also functions as a system that allows for mixing strings of various
origins and to make them safe for the requested enviroment.

Currently the goal is to verify that strings never create unintended issues like
cross site scripting, json injection and similar.

The premise is that all strings coming from the web-user, eg form inputs,
headers, remote api's, database fields and config files are unsafe by definition
 and that all consumers of strings upgrade to their respective safe string
 variant at ingestion.

Consumers like template parsers know what the intended working environment for a
 string is going to be, eg, html. And thus can decide on escaping if the handed
 object is not of a type known to be safe for that environment.

Additions of unsafe types to a safe type automatically escape up to the safe
type. Handy escape() functions are present to do manual escaping if required.
"""

#TODO: logger geen enters
#bash injection 
#mysql escaping
__author__ = 'Jan Klopper (jan@underdark.nl)'
__version__ = 0.1

import html
import json
import urllib.parse as urlparse
import re
from ast import literal_eval
from sqlalchemy import text

class Basesafestring(str):
  """Base safe string class
  This does not signal any safety against injection itself, use the child
  classes instead!"""
  ""
  def __add__(self, other):
    """Adds a second string to this string, upgrading it in the process"""
    data = ''.join(( # do not use the __add__ since that creates a loop
        self, # the original item
        self.__upgrade__(other)))
    return self.__class__(data)

  def __upgrade__(self, other):
    """Upgrade a given object to be as safe, and in the same safety context as
    the current object"""
    if type(other) == self.__class__: #same type, easy, lets add
      return other
    elif isinstance(other, Basesafestring): # lets unescape the other 'safe' type,
      otherdata = other.unescape(other) # its escaping is not needed for his context
      return self.escape(otherdata) # escape it using our context
    else:
      return self.escape(str(other)) # escape it using our context

  def __new__(cls, data, **kwargs):
    return super().__new__(cls,
        cls.escape(cls, str(data)) if 'unsafe' in kwargs else data)

  def __str__(self):
    if self.__class__ == Basesafestring:
      raise NotImplementedError
    return super().__str__()

  def __repr__(self):
    if self.__class__ == Basesafestring:
      raise NotImplementedError
    return super().__repr__()

  def format(self, *args, **kwargs):
    args = list(map(self.__upgrade__, args))
    kwargs = {k: self.__upgrade__(v) for k, v in kwargs.items()}
    return super().format(*args, **kwargs)

  def escape(self, data):
    raise NotImplementedError

  def unescape(self, data):
    raise NotImplementedError


class SQLSAFE(Basesafestring):
  CHARS_ESCAPE_DICT = {
    '\0'   : '\\0',
    '\b'   : '\\b',
    '\t'   : '\\t',
    '\n'   : '\\n',
    '\r'   : '\\r',
    '\x1a' : '\\Z',
    '"'    : '\\"',
    '\''   : '\\\'',
    '\\'   : '\\\\'
  }
  CHARS_ESCAPE_REGEX = re.compile(r"""[\0\b\t\n\r\x1a\"\'\\]""")
  PLACEHOLDERS_REGEX = re.compile(r"""\?+""")
  QUOTES_REGEX = re.compile(r"""([\"'])(?:(?=(\\?))\2.)*?\1""", re.DOTALL)

  def __new__(cls, data, *args, **kwargs):
    return super().__new__(cls,
        cls.escape(cls, str(data), args) if 'unsafe' in kwargs else data)

  def __upgrade__(self, other):
      """Upgrade a given object to be as safe, and in the same safety context as
      the current object"""
      if type(other) == self.__class__: #same type, easy, lets add
        return other
      elif isinstance(other, Basesafestring): # lets unescape the other 'safe' type,
        otherdata = other.unescape(other) # its escaping is not needed for his context
        return self.escape(otherdata) # escape it using our context
      else:
        index = 0
        escaped = ""
        print(self.sanitize(other))
        # for m in self.QUOTES_REGEX.finditer(other):
        #   escaped += other[index:m.span()[0]] + self.sanitize(m.group()[1:-1])
        #   index = m.span()[1]
        # escaped += other[index:]
        return escaped

  @classmethod
  def sanitize(cls, value):
    index = 0
    escaped = ""
    if len(cls.CHARS_ESCAPE_REGEX.findall(value)) == 0:
      if not str.isdigit(value):
        return f"'{value}'"
      return value
    for m in cls.CHARS_ESCAPE_REGEX.finditer(value):
      print(value[index:m.span()[0]])
      escaped += value[index:m.span()[0]] + cls.CHARS_ESCAPE_DICT[m.group()]
      index = m.span()[1]
    escaped += value[index:]
    if not str.isdigit(escaped):
      return f"'{escaped}'"
    return escaped

  def escape(cls, sql, values):
    x = 0
    escaped = ""
    if not isinstance(values, tuple):
      raise ValueError("Values should be a tuple")
    if len(cls.PLACEHOLDERS_REGEX.findall(sql)) != len(values):
      raise ValueError("Number of values does not match number of replacements")
    for index, m in enumerate(cls.PLACEHOLDERS_REGEX.finditer(sql)):
      escaped += sql[x:m.span()[0]] + cls.sanitize(values[index])
      x = m.span()[1]
    escaped += sql[x:]
    return SQLSAFE(escaped)
    
    
# what follows are the actual useable classes that are safe in specific contexts
class HTMLsafestring(Basesafestring):
  """This class signals that the content is HTML safe"""
 
    
  def escape(self, data):
    return html.escape(data)

  def unescape(self, data):
    return html.unescape(data)


class JSONsafestring(Basesafestring):
  """This class signals that the content is JSON safe

  Most of this will be handled by just feeding regular python objects into
  json.dumps, but for some outputs this might be handy. Eg, when outputting
  partial json into dynamic generated javascript files"""

  def escape(self, data):
    if not isinstance(data, str):
      raise TypeError
    return json.dumps(data)

  def unescape(self, data):
    if not isinstance(data, str):
      raise TypeError
    data = json.loads(data)
    return data


class URLqueryargumentsafestring(Basesafestring):
  """This class signals that the content is URL query argument safe"""

  def escape(self, data):
    """Encode any non url argument chars"""
    return urlparse.quote_plus(data)

  def unescape(self, data):
    """Decode any encoded non url argument chars"""
    return urlparse.unquote_plus(data)


class URLsafestring(Basesafestring):
  """This class signals that the content is URL safe, for use in http headers
  like redirects, but also calls to wget or the like"""

  def escape(self, data):
    """Drops everything that does not fit in a url

    Since urlparse does not filter out new line chars well do that ourselves

    http://www.ietf.org/rfc/rfc1738.txt
    http://www.ietf.org/rfc/rfc2396.txt
    http://www.ietf.org/rfc/rfc3986.txt
    https://tools.ietf.org/html/rfc3986#section-2 uri chars
    """
    if '\n' in data or '\r' in data:
      data = data.splitlines()[0]
    return urlparse.urlparse(data).geturl()

  def unescape(self, data):
    """Can't unremove non url elements so we'll just return the string"""
    return data


class EmailAddresssafestring(Basesafestring):
  """This class signals that the content is safe Email address

  ITs usefull when sending out emails or constructing email headers
  Email Header injection is subverted."""

  def escape(self, data):
    """Drops everything that does not fit in an email address"""
    regex = re.compile(r'''(
        [a-zA-Z0-9._%+-]+ # username
        @ # @ symbol
        ([a-zA-Z0-9.-]+) # domain name
        (\.[a-zA-Z]{2,4}) # dot-something
    )''', re.VERBOSE)
    return regex.search(data).group()

  def unescape(self, data):
    """Can't unremove non address elements so we'll just return the string"""
    return data
