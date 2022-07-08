#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Tests for the request module."""

# Method could be a function
# pylint: disable-msg=R0201

# Too many public methods
# pylint: disable-msg=R0904

# Standard modules
import unittest
import io as stringIO
from typing import Union
from itertools import zip_longest

import urllib
from functools import wraps
from urllib.parse import urlencode

# Unittest target
from uweb3 import request


def CreateRequest(headers: Union[dict, None] = None):
    default_headers = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "path",
        "QUERY_STRING": "",
        "HTTP_X_FORWARDED_FOR": "127.0.0.1",
        "HTTP_HOST": "test",
    }
    if headers:
        default_headers.update(headers)

    return request.Request(
        default_headers,
        None,
        None,
    )


def parameterize(params: str, values):
    """Decorator that can be used like pytest.mark.parameterize."""

    def decorator(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            parameters = [x.strip() for x in params.split(",")]

            for item in values:
                fun(*args, **dict(zip_longest(parameters, item)), **kwargs)

        return wrapper

    return decorator


class IndexedFieldStorageTest(unittest.TestCase):
    """Comprehensive testing of the IndexedFieldStorage object."""

    def CreateFieldStorage(self, data):
        """Returns an IndexedFieldStorage object constructed from the given data."""
        return request.IndexedFieldStorage(
            stringIO.StringIO(data), environ={"REQUEST_METHOD": "POST"}
        )

    def testEmptyStorage(self):
        """An empty IndexedFieldStorage is empty and is boolean False"""
        ifs = self.CreateFieldStorage("")
        self.assertFalse(ifs)

    def testBasicStorage(self):
        """A basic IndexedFieldStorage has the proper key + value pair"""
        ifs = self.CreateFieldStorage("key=value")
        self.assertEqual(ifs.getfirst("key"), "value")
        self.assertEqual(ifs.getlist("key"), ["value"])

    def testMissingKey(self):
        """getfirst / getlist for missing keys return proper defaults"""
        ifs = self.CreateFieldStorage("")
        self.assertEqual(ifs.getfirst("missing"), None)
        self.assertEqual(ifs.getfirst("missing", "signal"), "signal")
        self.assertEqual(ifs.getlist("missing"), [])
        # getlist has no default argument

    def testMultipleKeyOrder(self):
        """getlist returns keys in the order they were given to the FieldStorage"""
        args = ["1", "3", "2"]
        ifs = self.CreateFieldStorage("arg=1&arg=3&arg=2")
        self.assertEqual(ifs.getlist("arg"), args)

    def testUrlEncoding(self):
        """IndexedFieldStorage can handle utf-8 encoded forms"""
        string = "We ♥ Unicode"
        try:
            data = urllib.urlencode({"q": string})
        except AttributeError:
            data = urllib.parse.urlencode({"q": string})
        ifs = self.CreateFieldStorage(data)
        self.assertEqual(ifs.getfirst("q"), string)

    def testDictionaryFunctionality(self):
        """The indexing of IndexedFieldStorage allows dict-like assignment"""
        data = "d[name]=Arthur&d[type]=King"
        ifs = self.CreateFieldStorage(data)
        self.assertEqual(ifs.getfirst("d"), {"name": "Arthur", "type": "King"})

    def testDictionaryAndMultipleValues(self):
        """Dictionaries and regular values can be combined; dict is item no. #1"""
        data = "d=third&d[first]=1&d[second]=2&d=fourth"
        ifs = self.CreateFieldStorage(data)
        form_data = ifs.getlist("d")
        self.assertEqual(form_data[0], {"first": "1", "second": "2"})
        self.assertEqual(form_data[1], "third")
        self.assertEqual(form_data[2], "fourth")

    def testRequestCorrectValues(self):
        """Validate that the attributes on the request object are set accordingly"""
        req = CreateRequest()
        self.assertEqual(req.method, "GET")
        self.assertEqual(req.path, "path")
        self.assertEqual(req.env["HTTP_X_FORWARDED_FOR"], "127.0.0.1")
        self.assertEqual(req.env["HTTP_HOST"], "test")

    def testGetQueryString(self):
        """Validate that the request GET parameters are parsed correctly"""
        req = CreateRequest({"QUERY_STRING": "foo=hello&bar=world"})
        self.assertDictEqual(req.vars["get"], {"foo": ["hello"], "bar": ["world"]})

    def testGetQueryStringMultiple(self):
        """Validate that the request GET parameters are parsed correctly"""
        req = CreateRequest({"QUERY_STRING": "d=third&d[first]=1&d[second]=2&d=fourth"})
        self.assertDictEqual(
            req.vars["get"],
            {"d": ["third", "fourth"], "d[first]": ["1"], "d[second]": ["2"]},
        )

    def testHeadersFromEnv(self):
        """Validate that HTTP_XXX_XXX headers are converted to XXX-XXX"""
        result = dict(
            request.headers_from_env(
                {
                    "HTTP_CONTENT_TYPE": "ctype",
                    "HTTP_X_FORWARD_FOR": "forward",
                    "HTTP_HOST": "host",
                }
            )
        )
        self.assertEqual(
            result,
            {"content-type": "ctype", "x-forward-for": "forward", "host": "host"},
        )

    def testCookie(self):
        """Validate that the HTTP_COOKIE header is parsed correctly"""
        req = CreateRequest(
            {"HTTP_COOKIE": "cookie=first_cookie;another_cookie=second_cookie"}
        )
        self.assertDictEqual(
            req.vars["cookie"],
            {"cookie": "first_cookie", "another_cookie": "second_cookie"},
        )

    @parameterize(
        "input, expected, content_length",
        [
            ({"username": "username"}, {"u": ""}, 1),
            ({"username": "username"}, {"us": ""}, 2),
            ({"username": "username"}, {"username": "u"}, 10),
            ({"username": "username"}, {"username": "username"}, 17),
        ],
    )
    def testReadLimited(self, input, expected, content_length):
        """Validate that the request does not read further than the
        specified content-length header"""
        data = urlencode(input)
        fp = stringIO.BytesIO(data.encode())

        req = CreateRequest(
            {
                "wsgi.input": fp,
                "CONTENT_LENGTH": content_length,
                "REQUEST_METHOD": "POST",
            }
        )
        req.process_request()

        post_data = req.vars["post"]
        self.assertEqual(post_data.__dict__, expected)

    def testMissingContentLengthHeader(self):
        """Validate that an error is raised when attempting to post data
        without a content-length header present"""
        data = urlencode({"username": "username"})
        fp = stringIO.BytesIO(data.encode())

        req = CreateRequest(
            {
                "wsgi.input": fp,
                "REQUEST_METHOD": "POST",
            }
        )
        with self.assertRaises(request.MissingContentLengthError):
            req.process_request()

    def testInvalidContentLengthHeader(self):
        data = urlencode({"username": "username"})
        fp = stringIO.BytesIO(data.encode())

        req = CreateRequest(
            {
                "wsgi.input": fp,
                "REQUEST_METHOD": "POST",
                "CONTENT_LENGTH": "invalid format",
            }
        )
        with self.assertRaises(request.InvalidContentLengthError):
            req.process_request()


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
