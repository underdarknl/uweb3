#!/usr/bin/python3
"""Tests for the safestring code"""
__author__ = 'Jan Klopper (jan@underdark.nl)'
__version__ = 0.1

# default modules
import unittest

#custom modules
from uweb3.ext_lib.libs.safestring import URLsafestring, SQLSAFE, HTMLsafestring, URLqueryargumentsafestring, JSONsafestring, EmailAddresssafestring, Basesafestring

class BasesafestringMethods(unittest.TestCase):
  def test_creation_str(self):
    with self.assertRaises(NotImplementedError) as context:
      str(Basesafestring('foo'))
    self.assertEqual(NotImplementedError, type(context.exception))

  def test_creation_repr(self):
    with self.assertRaises(NotImplementedError) as context:
      repr(Basesafestring('foo'))
    self.assertEqual(NotImplementedError, type(context.exception))


class TestHTMLStringMethods(unittest.TestCase):
  def test_init(self):
    testdata = HTMLsafestring('foo<test>')
    self.assertEqual(testdata, 'foo<test>')

  def test_init_unsafe(self):
    testdata = HTMLsafestring('foo<test>', unsafe=True)
    self.assertEqual(testdata, 'foo&lt;test&gt;')

  def test_addition(self):
    testdata = HTMLsafestring('foo') + '<b>test'
    self.assertEqual(testdata, 'foo&lt;b&gt;test')

  def test_addition_quotes(self):
    testdata = HTMLsafestring('foo') + '"test"'
    self.assertEqual(testdata, 'foo&quot;test&quot;')

  def test_addition_same(self):
    testdata = HTMLsafestring('foo<test>') + HTMLsafestring('foo<test>')
    self.assertEqual(testdata, 'foo<test>foo<test>')

  def test_addition_same_escaped(self):
    testdata = HTMLsafestring('foo') + '<test>'
    testdata = testdata + HTMLsafestring('foo<test>')
    self.assertEqual(testdata, 'foo&lt;test&gt;foo<test>')

  def test_addition_other(self):
    testdata = HTMLsafestring('foo<test>')
    urlquery = URLqueryargumentsafestring('foo') + ' test test/test'
    self.assertEqual(testdata + urlquery, 'foo<test>foo test test/test')

  def test_format(self):
    testdata = HTMLsafestring('foo<test> {} test').format('<b>')
    self.assertEqual(testdata, 'foo<test> &lt;b&gt; test')

  def test_format_nested_safesametype(self):
    testdata = HTMLsafestring('test {} {}').format(
      '<b>', HTMLsafestring('<b>'))
    self.assertEqual(testdata, 'test &lt;b&gt; <b>')

  def test_format_nested_safeothertype(self):
    testdata = HTMLsafestring('test {} {}').format(
      '<b>', EmailAddresssafestring('<b>'))
    self.assertEqual(testdata, 'test &lt;b&gt; &lt;b&gt;')

  def test_format_keyword(self):
    testdata = HTMLsafestring('foo<test> {kw} test').format(kw='<b>')
    self.assertEqual(testdata, 'foo<test> &lt;b&gt; test')


class TestJSonStringMethods(unittest.TestCase):
  def test_addition(self):
    testdata = JSONsafestring('foo') + '"test"'
    self.assertEqual(testdata, 'foo"\\"test\\""')

class TestURLqueryargumentsafestringMethods(unittest.TestCase):
  def test_addition(self):
    testdata = URLqueryargumentsafestring('foo') + 'test test/test'
    self.assertEqual(testdata, 'footest+test%2Ftest')


class TestURLsafestringMethods(unittest.TestCase):
  def test_headerinjection(self):
    """See if we correctly clean up header injection attemps"""
    testdata = URLsafestring('https://underdark.nl/somefile\n\nlocation: http://attacker.nl', unsafe=True)
    self.assertEqual(str(testdata), 'https://underdark.nl/somefile')

  def test_validurlunwisechars(self):
    url = 'http://mw1.google.com/mw-earth-vectordb/kml-samples/gp/seattle/gigapxl/$[level]/r$[y]_c$[x].jpg#fragment'
    testdata = URLsafestring(url, unsafe=True)
    self.assertEqual(str(testdata), url)

class TestEmailAddresssafestringMethods(unittest.TestCase):
  def test_unsafe_init(self):
    """See if we correctly clean up header injection attemps"""
    testdata = EmailAddresssafestring('jan@underdark.nl\nbcc: victim@otherhost.com', unsafe=True)
    self.assertEqual(testdata, 'jan@underdark.nl')

class TestSQLSAFEMethods(unittest.TestCase):
  def test_escaping(self):
    testdata = SQLSAFE("""SELECT * FROM users WHERE username = ?""", values=("username'",), unsafe=True)
    self.assertEqual(testdata, "SELECT * FROM users WHERE username = 'username\\''")
    testdata = SQLSAFE("""SELECT * FROM users WHERE username = ?""", values=('username"',), unsafe=True)
    self.assertEqual(testdata, "SELECT * FROM users WHERE username = 'username\\\"'")
    testdata = SQLSAFE("""SELECT * FROM users WHERE username = ? AND ? """, values=('username"', "password"), unsafe=True)

  def test_concatenation(self):
    testdata = SQLSAFE("""SELECT * FROM users WHERE username = ?""", values=("username'",), unsafe=True)
    other = "AND firstname='test'"
    self.assertEqual(testdata + other, "SELECT * FROM users WHERE username = 'username\\'' AND firstname=\\'test\\'")
    testdata = SQLSAFE("""SELECT * FROM users WHERE username = ?""", values=('username"',), unsafe=True)
    other = "AND firstname='test'"
    self.assertEqual(testdata + other, "SELECT * FROM users WHERE username = 'username\\\"' AND firstname=\\'test\\'")

  # def test_unescape_wrong_type(self):
  #   """Validate if the string we are trying to unescape is part of an SQLSAFE instance"""
  #   testdata = SQLSAFE("""SELECT * FROM users WHERE username = ?""", values=("username'",), unsafe=True)
  #   with self.assertRaises(ValueError) as msg:
  #     self.assertRaises(testdata.unescape('whatever'))

  def test_unescape(self):
    testdata = SQLSAFE("""SELECT * FROM users WHERE username = ?""", values=("username\\t \\0",), unsafe=True)
    testdata.unescape(testdata)


if __name__ == '__main__':
    unittest.main()
