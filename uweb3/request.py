#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""µWeb3 request module."""

# Standard modules
import cgi
import http.cookies as cookie
import io as stringIO
import json
import re
import tempfile
from typing import Union
import typing
from urllib.parse import parse_qs, parse_qsl

# uWeb modules
from . import response


def headers_from_env(env):
    for key, value in env.items():
        if key.startswith("HTTP_"):
            yield key[5:].lower().replace("_", "-"), value


class CookieTooBigError(Exception):
    """Error class for cookie when size is bigger than 4096 bytes"""


class Cookie(cookie.SimpleCookie):
    """Cookie class that uses the most specific value for a cookie name.

    According to RFC2965 (http://tools.ietf.org/html/rfc2965):
        If multiple cookies satisfy the criteria above, they are ordered in
        the Cookie header such that those with more specific Path attributes
        precede those with less specific.  Ordering with respect to other
        attributes (e.g., Domain) is unspecified.

    This class adds this behaviour to cookie parsing. That is, a key:value pair
    WILL NOT overwrite an already existing (and thus more specific) pair.

    N.B.: this class assumes the given cookie to follow the standards outlined in
    the RFC. At the moment (2011Q1) this assumption proves to be correct for both
    Chromium (and likely Webkit in general) and Firefox. Other browsers have not
    been tested, and might possibly deviate from the suggested standard.
    As such, it's recommended not to re-use the cookie name with different values
    for different paths.
    """

    # Unfortunately this works by redefining a private method.
    def _BaseCookie__set(self, key, real_value, coded_value):
        """Inserts a morsel into the Cookie, strictly on the first occurrance."""
        if key not in self:
            morsel = cookie.Morsel()
            morsel.set(key, real_value, coded_value)
            dict.__setitem__(self, key, morsel)


class BaseRequest:
    MAX_COOKIE_LENGTH: int = 4 * 1024  # 4KB
    MAX_REQUEST_BODY_SIZE: int = 20 * 1024 * 1024  # 20MB

    def __init__(self, env):
        self.env = env
        self.charset = "utf-8"
        self.headers = dict(headers_from_env(env))
        self.noparse = self.headers.get("accept", "").lower() == "application/json"

        self.env["host"] = self.headers.get("Host", "").strip().lower()
        self.env["REAL_REMOTE_ADDR"] = self._return_real_remote_addr()
        self.env["mimetype"] = self._get_mimetype()

        self.method = self.env["REQUEST_METHOD"]
        self.path = self.env["PATH_INFO"]

        self.vars = {
            "cookie": {
                name: value.value
                for name, value in Cookie(self.env.get("HTTP_COOKIE")).items()
            },
            "get": QueryArgsDict(parse_qs(self.env["QUERY_STRING"])),
            "post": IndexedFieldStorage(),
            "put": IndexedFieldStorage(),
            "delete": IndexedFieldStorage(),
            "files": IndexedFieldStorage(),
        }

    def _get_mimetype(self):
        return self.env.get("CONTENT_TYPE", "").split(";")[0]

    def _return_real_remote_addr(self):
        """Returns the remote ip-address,
        if there is a proxy involved it will take the last IP addres from the HTTP_X_FORWARDED_FOR list
        """
        try:
            return self.env["HTTP_X_FORWARDED_FOR"].split(",")[-1].strip()
        except KeyError:
            return self.env["REMOTE_ADDR"]


class DataParser:
    def __init__(
        self,
        env,
        max_size: int,
        content_length: int,
        charset: str,
    ):
        self.env = env
        self.charset = charset
        self.input = env["wsgi.input"]
        self.mimetype = env["mimetype"]

        self.max_size = max_size
        self.content_length = content_length
        self.request_payload = None
        self._parse_functions = {
            "application/json": self._parse_multipart,
            "multipart/form-data": self._parse_json,
            "application/x-www-form-urlencoded": self._parse_urlencoded,
        }

    def parse(self):
        # TODO: Handle streams
        handler = self._parse_functions.get(self.mimetype, self._parse_regular)
        print(self.content_length)
        self.request_payload = self.input.read(min(self.content_length, self.max_size))
        print(self.max_size)
        print(len(self.request_payload))
        return handler()
        # return self.request_payload

    def _parse_multipart(self):
        temp_file = tempfile.TemporaryFile()
        temp_file.write(self.request_payload)
        temp_file.seek(0)
        return IndexedFieldStorage(temp_file, environ=self.env, keep_blank_values=True)

    def _parse_json(self):
        try:
            return json.loads(self.request_payload)
        except (json.JSONDecodeError, ValueError):
            pass

    def _parse_urlencoded(self):
        return self._parse_regular()

    def _parse_regular(self):
        return IndexedFieldStorage(
            stringIO.StringIO(self.request_payload.decode(self.charset)),
            environ={"REQUEST_METHOD": "POST"},
        )


class Request(BaseRequest):
    def __init__(
        self,
        env,
        logger,
        errorlogger,
    ):  # noqa: C901
        super().__init__(env=env)
        self._out_headers = []
        self._out_status = 200
        self._response = None
        self.logger = logger
        self.errorlogger = errorlogger

        if self.method in ("POST", "PUT", "DELETE"):
            self.process_request()

    def process_request(self):
        if "CONTENT_LENGTH" not in self.env:
            # We should not allowed requests where CONTENT_LENGTH is not specified
            # https://peps.python.org/pep-3333#specification-details
            # TODO: Throw error and log
            raise NotImplementedError()

        content_length = self.env["CONTENT_LENGTH"]

        try:
            content_length = int(content_length)
        except Exception:
            # TODO: If CONTENT_LENGTH is not a valid integer stop processing here.
            raise NotImplementedError()

        parser = DataParser(
            env=self.env,
            max_size=self.MAX_REQUEST_BODY_SIZE,
            content_length=content_length,
            charset=self.charset,
        )
        self.vars[self.method.lower()] = parser.parse()

    @property
    def response(self):
        if self._response is None:
            self._response = response.Response(headers=self._out_headers)
        return self._response

    def Redirect(self, location, httpcode=307):
        REDIRECT_PAGE = (
            "<!DOCTYPE html><html><head><title>Page moved</title></head>"
            '<body>Page moved, please follow <a href="{}">this link</a>'
            "</body></html>"
        ).format(location)

        headers = {"Location": location}
        if self.response.headers.get("Set-Cookie"):
            headers["Set-Cookie"] = self.response.headers.get("Set-Cookie")
        return response.Response(
            content=REDIRECT_PAGE,
            content_type=self.response.headers.get("Content-Type", "text/html"),
            httpcode=httpcode,
            headers=headers,
        )

    def AddCookie(self, key, value, **attrs):
        """Adds a new cookie header to the response.

        Arguments:
          @ key: str
            The name of the cookie.
          @ value: str
            The actual value to store in the cookie.
          % expires: str ~~ None
            The date + time when the cookie should expire. The format should be:
            "Wdy, DD-Mon-YYYY HH:MM:SS GMT" and the time specified in UTC.
            The default means the cookie never expires.
            N.B. Specifying both this and `max_age` leads to undefined behavior.
          % path: str ~~ '/'
            The path for which this cookie is valid. This default ('/') is different
            from the rule stated on Wikipedia: "If not specified, they default to
            the domain and path of the object that was requested".
          % domain: str ~~ None
            The domain for which the cookie is valid. The default is that of the
            requested domain.
          % max_age: int
            The number of seconds this cookie should be used for. After this period,
            the cookie should be deleted by the client.
            N.B. Specifying both this and `expires` leads to undefined behavior.
          % secure: boolean
            When True, the cookie is only used on https connections.
          % httponly: boolean
            When True, the cookie is only used for http(s) requests, and is not
            accessible through Javascript (DOM).
        """
        if (
            isinstance(value, (str))
            and len(value.encode("utf-8")) >= self.MAX_COOKIE_LENGTH
        ):
            raise CookieTooBigError(
                "Cookie is larger than %d bytes and wont be set"
                % self.MAX_COOKIE_LENGTH
            )

        new_cookie = Cookie({key: value})
        if "max_age" in attrs:
            attrs["max-age"] = attrs.pop("max_age")
        new_cookie[key].update(attrs)
        if "samesite" not in attrs and "secure" not in attrs:
            try:  # only supported from python 3.8 and up
                attrs[
                    "samesite"
                ] = "Lax"  # set default to LAX for no secure (eg, local) sessions.
            except cookie.CookieError:
                pass
        self.AddHeader("Set-Cookie", new_cookie[key].OutputString())

    def AddHeader(self, name, value):
        if name == "Set-Cookie":
            if not self.response.headers.get("Set-Cookie"):
                self.response.headers["Set-Cookie"] = [value]
                return
            self.response.headers["Set-Cookie"].append(value)
            return
        self.response.AddHeader(name, value)

    def DeleteCookie(self, name):
        """Deletes cookie by name

        Arguments
        @ name: str
        """
        self.AddHeader(
            "Set-Cookie",
            "{}=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT;".format(name),
        )


class IndexedFieldStorage(cgi.FieldStorage):
    """Adaption of cgi.FieldStorage with a few specific changes.

    Notable differences with cgi.FieldStorage:
      1) `environ.QUERY_STRING` does not add to the returned FieldStorage
         This way we maintain a strict separation between POST and GET variables.
      2) Field names in the form 'foo[bar]=baz' will generate a dictionary:
           foo = {'bar': 'baz'}
         Multiple statements of the form 'foo[%s]' will expand this dictionary.
         Multiple occurrances of 'foo[bar]' will result in unspecified behavior.
      3) Automatically attempts to parse all input as UTF8. This is the proposed
         standard as of 2005: http://tools.ietf.org/html/rfc3986.
    """

    FIELD_AS_ARRAY = re.compile(r"(.*)\[(.*)\]")

    def iteritems(self):
        return ((key, self.getlist(key)) for key in self)

    def items(self):
        return list(self.iteritems())

    def read_urlencoded(self):
        indexed = {}
        self.list = []
        for field, value in parse_qsl(
            self.fp.read(self.length), self.keep_blank_values, self.strict_parsing
        ):
            if self.FIELD_AS_ARRAY.match(str(field)):
                field_group, field_key = self.FIELD_AS_ARRAY.match(field).groups()
                indexed.setdefault(field_group, cgi.MiniFieldStorage(field_group, {}))
                indexed[field_group].value[field_key] = value
            else:
                self.list.append(cgi.MiniFieldStorage(field, value))
        self.list = list(indexed.values()) + self.list
        self.skip_lines()

    def __repr__(self):
        if self.filename:
            return "%s({filename: %s, value: %s, file: %s})" % (
                self.__class__.__name__,
                self.filename,
                self.value,
                self.file,
            )
        return "{%s}" % ",".join(
            "'%s': '%s'" % (k, v if len(v) > 1 else v[0]) for k, v in self.iteritems()
        )

    @property
    def __dict__(self):
        return {
            key: value if len(value) > 1 else value[0]
            for key, value in self.iteritems()
        }


class QueryArgsDict(dict):
    def getfirst(self, key, default=None):
        """Returns the first value for the requested key, or a fallback value."""
        try:
            return self[key][0]
        except KeyError:
            return default

    def getlist(self, key):
        """Returns a list with all values that were given for the requested key.

        N.B. If the given key does not exist, an empty list is returned.
        """
        try:
            return self[key]
        except KeyError:
            return []
