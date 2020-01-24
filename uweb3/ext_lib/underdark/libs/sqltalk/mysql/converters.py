#!/usr/bin/python2.5
"""MySQLdb type conversion module

This module handles all the type conversions for MySQL. If the default
type conversions aren't what you need, you can make your own. The
dictionary conversions maps some kind of type to a conversion function
which returns the corresponding value:

Key: FIELD_TYPE.* (from MySQLdb.constants)

Conversion function:

  Arguments: string

  Returns: Python object

Key: Python type object (from types) or class

Conversion function:

  Arguments: Python object of indicated type or class AND
         conversion dictionary

  Returns: SQL literal value

  Notes: Most conversion functions can ignore the dictionary, but
       it is a required parameter. It is necessary for converting
       things like sequences and instances.

Don't modify conversions if you can avoid it. Instead, make copies
(with the copy() method), modify the copies, and then pass them to
MySQL.connect().
"""

# Standard modules
import array
import datetime
import decimal
import time

# Application specific modules
from .. import sqlresult
from . import constants
from . import times


def Array2Str(obj, conv_dict):
  """Converts an array to a string."""
  return Thing2Literal(obj.tostring(), conv_dict)


def Bool2Str(obj, conv_dict=None):
  """Converts a bool to either 'True' or 'False' as string."""
  return str(obj)


def Float2Str(obj, conv_dict=None):
  """Converts a floating point number to a string."""
  return '%.15g' % obj


def Instance2Str(obj, conv_dict):
  """Convert an Instance to a string representation. If the __str__() method
  produces acceptable output, then you don't need to add the class to
  conversions; it will be handled by the default converter. If the exact class
  is not found in conv_dict, it will use the first class it can find for which
  obj is an instance.
  """
  if obj.__class__ in (object, type):
    return conv_dict[str](obj, conv_dict)
  try:
    return conv_dict[obj.__class__](obj, conv_dict)
  except KeyError:
    for converter in conv_dict:
      try:
        if (isinstance(obj, converter) and conv_dict[converter] is not Instance2Str):
          conv_dict[obj.__class__] = conv_dict[converter]
          return conv_dict[converter](obj, conv_dict)
      except TypeError:
        continue
    else:
      return conv_dict[str](obj, conv_dict)


def None2NULL(obj=None, conv_dict=None):
  """Convert None to NULL."""
  return 'NULL'


def Set2Str(obj, conv_dict):
  """Converts any itertable object into a comma separated string."""
  return escape_sequence(list(obj), conv_dict)


def Str2Set(string):
  """Converts a comma separated string back to a list."""
  return string.split(',')


def Thing2Literal(obj, conv_dict):
  """Convert something into a SQL string literal.  If using
  MySQL-3.23 or newer, string_literal() is a method of the
  _mysql.MYSQL object, and this function will be overridden with
  that method when the connection is created."""
  return "'%s'" % escape_string(str(obj))


def Thing2Str(obj, conv_dict=None):
  """Convert something into a string via str()."""
  return str(obj)

def escape_sequence(values, charset, mapping=None):
    escaped = []
    for item in values:
        quoted = escape_item(item, charset, mapping)
        escaped.append(quoted)
    return escaped

def escape_item(val, charset, mapping=None):
    if mapping is None:
        mapping = CONVERSIONS
    encoder = mapping.get(type(val))

    # Fallback to default when no encoder found
    if not encoder:
        try:
            encoder = mapping[str]
        except KeyError:
            raise TypeError("no default type converter defined")

    if encoder in (escape_dict, escape_sequence):
        val = encoder(val, charset, mapping)
    else:
        val = encoder(val, mapping)
    return val

def escape_dict(val, charset, mapping=None):
    n = {}
    for k, v in val.items():
        quoted = escape_item(v, charset, mapping)
        n[k] = quoted
    return n

def escape_string(value, mapping=None):
    """escape_string escapes *value* but not surround it with quotes.

    Value should be bytes or unicode.
    """
    if isinstance(value, str):
        return _escape_unicode(value)
    assert isinstance(value, (bytes, bytearray))
    value = value.replace('\\', '\\\\')
    value = value.replace('\0', '\\0')
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    value = value.replace('\032', '\\Z')
    value = value.replace("'", "\\'")
    value = value.replace('"', '\\"')
    return value

def _escape_unicode(value, mapping=None):
    """Escapes *value* without adding quote.

    Value should be unicode
    """
    return value.translate(ESCAPE_TABLE)


ESCAPE_TABLE = [chr(x) for x in range(128)]
ESCAPE_TABLE[0] = u'\\0'
ESCAPE_TABLE[ord('\\')] = u'\\\\'
ESCAPE_TABLE[ord('\n')] = u'\\n'
ESCAPE_TABLE[ord('\r')] = u'\\r'
ESCAPE_TABLE[ord('\032')] = u'\\Z'
ESCAPE_TABLE[ord('"')] = u'\\"'
ESCAPE_TABLE[ord("'")] = u"\\'"

CONVERSIONS = {
  sqlresult.ResultSet: escape_sequence,
  sqlresult.ResultRow: escape_dict,
  dict: escape_dict,
  list: escape_sequence,
  tuple: escape_sequence,
  set: Set2Str,
  bool: Bool2Str,
  int: Thing2Str,
  # long: Thing2Str,
  float: Float2Str,
  type(None): None2NULL,
  str: Thing2Literal,
  # unicode: Thing2Literal,
  object: Instance2Str,
  type: Instance2Str,
  array.array: Array2Str,
  datetime.datetime: times.DateTimeToLiteral,
  datetime.date: times.DateToLiteral,
  datetime.timedelta: times.TimeDeltaToLiteral,
  time.struct_time: times.TimeStructToLiteral,
  constants.FIELD_TYPE.TINY: int,
  constants.FIELD_TYPE.SHORT: int,
  # constants.FIELD_TYPE.LONG: long,
  constants.FIELD_TYPE.FLOAT: float,
  constants.FIELD_TYPE.DOUBLE: float,
  constants.FIELD_TYPE.DECIMAL: decimal.Decimal,
  constants.FIELD_TYPE.NEWDECIMAL: decimal.Decimal,
  # constants.FIELD_TYPE.LONGLONG: long,
  constants.FIELD_TYPE.INT24: int,
  constants.FIELD_TYPE.YEAR: int,
  constants.FIELD_TYPE.SET: Str2Set,
  constants.FIELD_TYPE.TIMESTAMP: times.MysqlTimestampConverter,
  constants.FIELD_TYPE.DATETIME: times.DateTimeOrNone,
  constants.FIELD_TYPE.TIME: times.TimeDeltaOrNone,
  constants.FIELD_TYPE.DATE: times.DateOrNone,
  constants.FIELD_TYPE.BLOB: str,
  constants.FIELD_TYPE.STRING: str,
  constants.FIELD_TYPE.VAR_STRING: str,
  constants.FIELD_TYPE.VARCHAR: str}
