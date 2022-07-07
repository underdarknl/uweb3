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


class RequestError(Exception):
    """Base class for request errors"""


class HeaderError(RequestError):
    """Base class for HTTP request header errors"""


class MissingContentLengthError(HeaderError):
    """Error that is raised when the CONTENT_LENGTH header is missing"""


class IncorrectContentLengthError(HeaderError):
    """Error that is raised when the supplied CONTENT_LENGTH does
    not match the provided data length."""


class InvalidContentLengthError(HeaderError):
    """Error that is raised when the provided CONTENT_LENGTH header
    is of an invalid format (non integer)."""


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


# This code is copied from the Werkzeug repository.
# https://github.com/pallets/werkzeug/blob/main/LICENSE.rst
# https://github.com/pallets/werkzeug/blob/d36aaf12b5d12634844e4c7f5dab4a8282688e12/src/werkzeug/wsgi.py#L828
class LimitedStream(io.IOBase):
    """Wraps a stream so that it doesn't read more than n bytes.  If the
    stream is exhausted and the caller tries to get more bytes from it
    :func:`on_exhausted` is called which by default returns an empty
    string.  The return value of that function is forwarded
    to the reader function.  So if it returns an empty string
    :meth:`read` will return an empty string as well.

    The limit however must never be higher than what the stream can
    output.  Otherwise :meth:`readlines` will try to read past the
    limit.

    .. admonition:: Note on WSGI compliance

       calls to :meth:`readline` and :meth:`readlines` are not
       WSGI compliant because it passes a size argument to the
       readline methods.  Unfortunately the WSGI PEP is not safely
       implementable without a size argument to :meth:`readline`
       because there is no EOF marker in the stream.  As a result
       of that the use of :meth:`readline` is discouraged.

       For the same reason iterating over the :class:`LimitedStream`
       is not portable.  It internally calls :meth:`readline`.

       We strongly suggest using :meth:`read` only or using the
       :func:`make_line_iter` which safely iterates line-based
       over a WSGI input stream.

    :param stream: the stream to wrap.
    :param limit: the limit for the stream, must not be longer than
                  what the string can provide if the stream does not
                  end with `EOF` (like `wsgi.input`)
    """

    def __init__(self, stream, limit: int) -> None:
        self._read = stream.read
        self._readline = stream.readline
        self._pos = 0
        self.limit = limit

    def __iter__(self) -> "LimitedStream":
        return self

    @property
    def is_exhausted(self) -> bool:
        """If the stream is exhausted this attribute is `True`."""
        return self._pos >= self.limit

    def on_exhausted(self) -> bytes:
        """This is called when the stream tries to read past the limit.
        The return value of this function is returned from the reading
        function.
        """
        # Read null bytes from the stream so that we get the
        # correct end of stream marker.
        return self._read(0)

    def on_disconnect(self):
        """What should happen if a disconnect is detected?  The return
        value of this function is returned from read functions in case
        the client went away.  By default a
        :exc:`~werkzeug.exceptions.ClientDisconnected` exception is raised.
        """
        raise ClientDisconnected()

    def exhaust(self, chunk_size: int = 1024 * 64) -> None:
        """Exhaust the stream.  This consumes all the data left until the
        limit is reached.

        :param chunk_size: the size for a chunk.  It will read the chunk
                           until the stream is exhausted and throw away
                           the results.
        """
        to_read = self.limit - self._pos
        chunk = chunk_size
        while to_read > 0:
            chunk = min(to_read, chunk)
            self.read(chunk)
            to_read -= chunk

    def read(self, size=None) -> bytes:
        """Read `size` bytes or if size is not provided everything is read.

        :param size: the number of bytes read.
        """
        if self._pos >= self.limit:
            return self.on_exhausted()
        if size is None or size == -1:  # -1 is for consistence with file
            size = self.limit
        to_read = min(self.limit - self._pos, size)
        try:
            read = self._read(to_read)
        except (OSError, ValueError):
            return self.on_disconnect()
        if to_read and len(read) != to_read:
            return self.on_disconnect()
        self._pos += len(read)
        return read

    def readline(self, size=None) -> bytes:
        """Reads one line from the stream."""
        if self._pos >= self.limit:
            return self.on_exhausted()
        if size is None:
            size = self.limit - self._pos
        else:
            size = min(size, self.limit - self._pos)
        try:
            line = self._readline(size)
        except (ValueError, OSError):
            return self.on_disconnect()
        if size and not line:
            return self.on_disconnect()
        self._pos += len(line)
        return line

    def readlines(self, size=None):
        """Reads a file into a list of strings.  It calls :meth:`readline`
        until the file is read to the end.  It does support the optional
        `size` argument if the underlying stream supports it for
        `readline`.
        """
        last_pos = self._pos
        result = []
        if size is not None:
            end = min(self.limit, last_pos + size)
        else:
            end = self.limit
        while True:
            if size is not None:
                size -= last_pos - self._pos
            if self._pos >= end:
                break
            result.append(self.readline(size))
            if size is not None:
                last_pos = self._pos
        return result

    def tell(self) -> int:
        """Returns the position of the stream.

        .. versionadded:: 0.9
        """
        return self._pos

    def __next__(self) -> bytes:
        line = self.readline()
        if not line:
            raise StopIteration()
        return line

    def readable(self) -> bool:
        return True


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
