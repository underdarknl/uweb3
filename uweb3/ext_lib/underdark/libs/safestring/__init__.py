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
  def __new__(cls, sql, *args, **kwargs):
    """Since the data should be in a tuple we dont need to parse it to a string"""
    #This is triggered if only a string is send to the method
    if 'unsafe' in kwargs:
      del kwargs['unsafe']
      #If the value is an unsafe string with no kwargs or data supplied
      if not kwargs and not args:
        #Put the string through this method to try and secure the query
        query, values = cls._find_vulnerabilities(cls, sql)
        return super().__new__(cls, 
                              cls.escape(cls, query, values))
      #If there is value and/or data then we use the scape function to put it in place
      #and escape the contents
      
      return super().__new__(cls, 
                             cls.escape(cls, sql, *args, **kwargs))
      
    if not kwargs and not args:
      if type(sql) == SQLSAFE:
        return sql
      #If only a string is supplied try and escure the query
      query, values = cls._find_vulnerabilities(cls, sql)
      return super().__new__(cls, 
                              cls.escape(cls, query, values)
                            )
    return super().__new__(cls,
                            cls.escape(cls, sql, *args, **kwargs)
                          )

  def __upgrade__(self, other):
    """Upgrade a given object to be as safe, and in the same safety context as
    the current object"""
    if isinstance(other, Basesafestring): # lets unescape the other 'safe' type,
      otherdata = other.unescape(other)
      return otherdata
    else:
      return other
    

  def __add__(self, other):
    """Adds a second string to this string, upgrading it in the process"""
    other = self.__upgrade__(other)
    return self.__class__("{}{}".format(self, other))

    
  def _find_vulnerabilities(self, query):
    """Method filters query and replaces all key=value values with escaped values
    Also check if the query is an insert. If so looks for the VALUES (val,val,val)
    and replaces all values with escaped values
    """
    placeholder_count = 0
    values = tuple()
    
    query = query.strip()
    #Looking for potential targets in the query. Splits everything with the name values
    targets = [(m.start(0), m.end(0)) for m in re.finditer("values", query.lower())]
    
    potential_payload = None
    for item in targets:
      string = None
      #Check if its either values( or values (
      if query[item[1]:len(query)][0] == "(":
        string = query[item[1]:len(query)]
      elif query[item[1] + 1:len(query)][0] == "(":
        string = query[item[1] + 1:len(query)]
      if string:
        if string[-1] == ")":
          potential_payload = string[1:-1]
          break
        match = re.search('\) ', string[1:])
        if match:
          potential_payload = string[1:match.span()[0] + 1]
          break
  
    if potential_payload:
      split_payload = potential_payload.split(',')
      placeholders = ''
      for i in range(len(split_payload)):
        placeholders += '{%s}' % placeholder_count
        if i < len(split_payload) - 1:
          placeholders += ','
        placeholder_count += 1
      query = query.replace(potential_payload, placeholders)
      for item in split_payload:
        item = item.strip()
        if item[0] == "'" or item[0] == '"':
          if item[-1] == "'" or item[-1] == '"':
            item = item[1:-1]
        values += (item,)
        
    results = re.findall("(\w+\s=\s\S+)|(\w+=\s\S+)|(\w+=\S+)", query)
    
    for item in results:
      value = None
      for match in item:
        if match is not "":
          value = match
      if value:
        placeholder = '{%s}' % placeholder_count
        key, v = value.split('=')
        values += (v.strip(), )
        new_value = "{key} = {value}".format(key=key.strip(), value=placeholder)
        query = query.replace(value, new_value)
        placeholder_count += 1
        
    return query, values

    
  def escape(self, sql, *args, **kwds):
    """Escapes the values part of the SQL string and makes sure it is impossible to 
    break out of the string. 
    
    Acts like python str.format() function. Accepts {0} and {key} like operators
    
    Example usage and output: 
    sql = SELECT * FROM users WHERE firstname={0} AND lastname={lastname}
    values = ("stef",)
    
    escape(sql, values, lastname="van Houten'); DROP TABLE users--;"); -->
    SELECT * FROM users 
    WHERE firstname='stef' 
    AND lastname="van Houten'); DROP TABLE users--;"
    
    Arguments:
      @ sql: string 
        SQL string with {index} as placeholder for the 'unsafe' values.
        Using muliple {index} with same index will replace all those with the same value
    """
    escaped = ()
    for value in args:
      escaped += (repr(value),)
      
    for key, value in kwds.items():
      kwds[key] = repr(value)
      
    return sql.format(*escaped, **kwds)



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
