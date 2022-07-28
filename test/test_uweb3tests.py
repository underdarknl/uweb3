#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""This script attempts to connect to the webserver running form this same
directory. It communicates over http and checks the output of each route.

You can start the webserver by issuing: python3 serve.py
You can test test all the functions by issuing: python3 testrunner.py -v
"""
import hashlib
import os
import unittest

import requests

baseurl = "http://127.0.0.1:8002/"
BASE_DIR = os.path.join(os.path.dirname(__file__), "uweb3tests")


def escape_html(string):
    """Quick and very dirty html escaping"""
    string = string.replace("'", "&#x27;")
    string = string.replace("<", "&lt;")
    string = string.replace(">", "&gt;")
    string = string.replace('"', "&quot;")
    return string


def HashContent(string):
    """Helper function for hashing of template files, this is needed to allow
    users to download raw templates on their own which they know the hash for."""
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


class ConfigTest(unittest.TestCase):
    """Test if the server is using the config file"""

    def test_port(self):
        """The config for the test server tells us we are live on 8002"""
        r = requests.get(baseurl)
        self.assertEqual(r.status_code, 200)


class ContentTests(unittest.TestCase):
    """Test the content of routes"""

    def test_content(self):
        """Lets see if the index route returns valid content"""
        r = requests.get(baseurl)
        self.assertEqual(r.encoding, "utf-8")
        with open(os.path.join(BASE_DIR, "templates/index.html"), "r") as template:
            templatecontent = template.read()
        self.assertEqual(r.status_code, 200)
        self.assertMultiLineEqual(templatecontent, r.text)

    def test_decorator_content(self):
        """Lets see if the template decorated route returns valid content"""
        url = baseurl + "templatedecorator"
        r = requests.get(url)
        self.assertEqual(r.encoding, "utf-8")
        with open(os.path.join(BASE_DIR, "templates/index.html"), "r") as template:
            templatecontent = template.read()
        self.assertEqual(r.status_code, 200)
        self.assertMultiLineEqual(templatecontent, r.text)

    def test_post(self):
        """Lets see if the posted data is reflected as json"""
        url = baseurl + "post"
        data = {"key": "value"}
        r = requests.post(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(r.json(), data)

    def test_returnNone(self):
        """Lets see if a None survives the response"""
        url = baseurl + "none"
        r = requests.get(url)
        response = "None"
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, response)

    def test_returnEmptystr(self):
        """Lets see if an Empty string survives the response"""
        url = baseurl + "emptystr"
        r = requests.get(url)
        response = ""
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, response)

    def test_templateparser(self):
        """This tests if the pagemaker can return dicts to the decorator,
        It tests if the _PostInit variables are present, and if the sparse list is
        populated based on the given tagname.
        It also tests if the content is properly escaped due to not being htmlSafe
        """
        url = baseurl + "templateglobals"
        r = requests.get(url)
        response = """path test<br>
sparse path test<br>
pagemaker return test<br>
&lt;b&gt;escaped html test&lt;/b&gt;"""

        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.text.startswith(response))

    @unittest.skip("Unknown encoding is broken since conversion to py3.")
    def test_unknown_encoding(self):
        """Lets see if our a record is served correctly as 'unknown' encoding"""
        url = baseurl + "mysql/read/1/unknown"
        r = requests.get(url)
        returnvalue = "Tank({'ID': 1, 'name': 'Living Room'})"
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, returnvalue)
        self.assertEqual(r.headers["Content-Type"], "unknown")


class HeadersTests(unittest.TestCase):
    """Test the headers"""

    def test_404(self):
        """Do we see 404 headers?"""
        url = baseurl + "nonexistant"
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)

    def test_redirect_headers(self):
        """Do we see redirect headers?"""
        url = baseurl + "redirect"
        r = requests.get(url, allow_redirects=False)
        self.assertEqual(r.status_code, 307)

    def test_redirect_location(self):
        """Do we see redirect headers?"""
        url = baseurl + "redirect"
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.url, baseurl)

    def test_post(self):
        """Lets see if the page returns a json/utf-8 content-type"""
        url = baseurl + "post"
        data = {"key": "value"}
        r = requests.post(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json; charset=utf-8")


class RouteTests(unittest.TestCase):
    """Test the method routing"""

    def test_text_get_optional_missing(self):
        """Lets see if the method route with GET returns valid content"""
        url = baseurl + "text/arguments/1/word"
        r = requests.get(url)
        response = """('1', 'word', 'test')"""
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, response)

    def test_text_get_optional(self):
        """Lets see if the method route with GET returns valid content"""
        url = baseurl + "text/arguments/1/word/optional"
        r = requests.get(url)
        response = """('1', 'word', 'optional')"""
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, response)


class MethodTests(unittest.TestCase):
    """Test the method routing"""

    def test_get(self):
        """Lets see if the method route with GET returns valid content"""
        url = baseurl + "method"
        r = requests.get(url)
        self.assertEqual(r.encoding, "utf-8")
        with open(os.path.join(BASE_DIR, "templates/index.html"), "r") as template:
            templatecontent = template.read()
        self.assertEqual(r.status_code, 200)
        self.assertMultiLineEqual(templatecontent, r.text)

    def test_post(self):
        """Lets see if the method route with POST returns a json reflection of our
        input"""
        url = baseurl + "method"
        data = {"key": "value"}
        r = requests.post(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), data)
        self.assertEqual(r.headers["Content-Type"], "application/json; charset=utf-8")

    def test_put(self):
        """Lets see if the method route with PUT returns the value from our put"""
        url = baseurl + "method"
        data = {"key": "value"}
        r = requests.put(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, data["key"])

    def test_put_keyerror(self):
        """Lets see if the method route with PUT returns the failover value from our put"""
        url = baseurl + "method"
        data = {"nokey": "value"}
        r = requests.put(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, "invalid")

    def test_del(self):
        """Lets see if the method route with DEL returns a text/plain content-type"""
        url = baseurl + "method"
        r = requests.delete(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, "delete done")
        self.assertEqual(r.headers["Content-Type"], "text/plain; charset=utf-8")


class CookieTests(unittest.TestCase):
    """Test the cookies."""

    def test_setcookie(self):
        """Lets see if cookieset route gives us a cookie."""
        url = baseurl + "cookie/set"
        data = '"this is an example cookie value set by uWeb"'
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.cookies["example"], data)

    def test_setsecurecookie(self):
        """Lets see if cookieset route gives us a cookie with the secure flag on."""
        url = baseurl + "cookie/set/secure"
        data = '"this is an example cookie value set by uWeb"'
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.cookies["example"], data)
        for cookie in r.cookies:
            self.assertTrue(cookie.secure)

    def test_setcookie_redirect(self):
        """Lets see if cookieset route gives us a cookie even after a redirect."""
        url = baseurl + "cookie/set/redirect"
        data = '"this is an example cookie value set by uWeb"'
        r = requests.get(url, allow_redirects=False)
        self.assertEqual(r.status_code, 307)
        self.assertEqual(r.cookies["example"], data)

    def test_templatedecoratedsetcookie(self):
        """Lets see if cookieset route gives us a cookie when combined with the template decorator."""
        url = baseurl + "cookie/set/templatedecorated"
        data = '"this is an example cookie value set by uWeb"'
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.cookies["example"], data)

    def test_reflectcookie(self):
        """Lets see if cookies are parsed and the value is reflected

        uWeb stores cookies quote encapsulated. But reads them without the quotes.
        """
        url = baseurl + "cookie/reflect"
        jar = requests.cookies.RequestsCookieJar()
        data = '"this is an example cookie value set by uWeb"'
        jar.set("cookie", data)
        r = requests.get(url, cookies=jar)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, data[1:-1])

    def test_secure_clear(self):
        """Lets see if we can set a cookie, and not have it reflected when we dont send it in for a second request."""

        url_set = baseurl + "signedcookie/set"
        requests.get(url_set)

        url_fetch = baseurl + "signedcookie/reflect"
        r_fetch = requests.get(url_fetch)

        self.assertEqual(r_fetch.text, "")
        self.assertEqual(r_fetch.cookies.keys(), [])
        self.assertEqual(r_fetch.status_code, 200)

    def test_secure_cookie(self):
        """Lets see if secure cookieset reflects our cookie when send ntampered for a second request.
        This also checks"""
        session = requests.session()

        url_set = baseurl + "signedcookie/set"
        r_set = session.get(url_set)

        url_fetch = baseurl + "signedcookie/reflect"
        r_fetch = session.get(url_fetch)

        content = escape_html("{'key': 'this is an example cookie value set by uWeb'}")
        self.assertEqual(r_fetch.text, content)
        self.assertEqual(r_set.cookies.keys(), ["signedExample"])
        self.assertEqual(r_fetch.status_code, 200)

    def test_secure_cookie_tampered(self):
        """Lets see if Signed cookieset route gives us a cookie even after a redirect."""
        jar = requests.cookies.RequestsCookieJar()
        jar.set("signedExample", "tampered")
        url_fetch = baseurl + "signedcookie/reflect"
        r_fetch = requests.get(url_fetch, cookies=jar)
        self.assertEqual(r_fetch.text, "")
        self.assertEqual(r_fetch.status_code, 200)


class StaticTests(unittest.TestCase):
    """Test the static handler."""

    def test_textfile(self):
        """Lets see if our text file is served correctly"""
        url = baseurl + "static/text.txt"
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text.rstrip(), "text content")
        self.assertEqual(r.headers["Content-Type"], "text/plain; charset=utf-8")

    def test_missingfile(self):
        """Lets see if our text file is served correctly"""
        url = baseurl + "static/invalid.txt"
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)

    def test_image(self):
        """Lets see if the image is returned"""
        url = baseurl + "static/favicon.png"
        r = requests.get(url)
        with open(os.path.join(BASE_DIR, "static/favicon.png"), "rb") as template:
            imagecontent = template.read()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, imagecontent)
        self.assertEqual(r.headers["Content-Type"], "image/png")

    def test_svgfile(self):
        """Lets see if our SVG file is served correctly"""
        url = baseurl + "static/SVG_Logo.svg"
        r = requests.get(url)
        with open(os.path.join(BASE_DIR, "static/SVG_Logo.svg"), "r") as template:
            svgcontent = template.read()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, svgcontent)
        self.assertEqual(r.headers["Content-Type"], "image/svg+xml")

    def test_xmlfile(self):
        """Lets see if our xml file is served correctly"""
        url = baseurl + "static/text.xml"
        r = requests.get(url)
        with open(os.path.join(BASE_DIR, "static/text.xml"), "r") as template:
            xmlcontent = template.read()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, xmlcontent)
        self.assertEqual(r.headers["Content-Type"], "application/xml")


class SQLitetests(unittest.TestCase):
    def test_record(self):
        """Lets see if our complete record is served correctly"""
        url = baseurl + "sqlite/read/1"
        r = requests.get(url)
        returnvalue = escape_html(
            """Fish({'ID': 1, 'name': 'sammy', 'species': 'shark', 'tank': Tank({'ID': 1, 'name': 'Living Room sqlite'})})"""
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, returnvalue)

    def test_missingfile(self):
        """Lets see if our missing record is served correctly"""
        url = baseurl + "sqlite/read/3"
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)


class Mysqltests(unittest.TestCase):
    def test_record(self):
        """Lets see if our complete record is served correctly"""
        url = baseurl + "mysql/read/1"
        r = requests.get(url)
        returnvalue = escape_html("""Tank({'ID': 1, 'name': 'Living Room'})""")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, returnvalue)

    def test_missingrecord(self):
        """Lets see if our missing record is served correctly"""
        url = baseurl + "mysql/read/-1"
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)

    def test_post_write(self):
        """Lets see if the page returns a posted and insterted mysql record"""
        url = baseurl + "mysql/write"
        data = {"name": "Squid Tank"}
        r = requests.post(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(escape_html("""'name': 'Squid Tank'""") in r.text)


class EscapingTest(unittest.TestCase):
    def test_get_optional_missing(self):
        """Lets see if the method route with GET returns valid content"""
        url = baseurl + "arguments/1/word"
        r = requests.get(url)
        response = escape_html("""('1', 'word', 'test')""")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, response)

    def test_get_optional(self):
        """Lets see if the method route with GET returns valid content"""
        url = baseurl + "arguments/1/word/optional"
        r = requests.get(url)
        response = escape_html("""('1', 'word', 'optional')""")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, response)

    def test_get_jsonstring(self):
        """Lets see if a string dumped ot trough the json headers is correctly escaped and encasulated in json"""
        url = baseurl + "jsonstring"
        r = requests.get(url)
        response = '{"message": "Hello, World!"}'
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), response)
        self.assertEqual(r.headers["Content-Type"], "application/json; charset=utf-8")

    def test_post_write_html_reflection(self):
        """Lets see if the page returns a posted and insterted mysql record"""
        url = baseurl + "mysql/write"
        data = {"name": "Squid <b>Tank</b>"}
        r = requests.post(url, data)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("<b>Tank</b>" not in r.text)


class ErrorTest(unittest.TestCase):
    def test_500(self):
        """Lets see if a deliberate error page is returned correctly."""
        url = baseurl + "error"
        response = escape_html("name 'test' is not defined")
        r = requests.get(url)
        self.assertEqual(r.status_code, 500)
        self.assertTrue(response in r.text)


class PathTraversalTest(unittest.TestCase):
    def test_500(self):
        """Lets see if a deliberate invalid template returns an error"""
        url = baseurl + "templatetraversal"
        response = escape_html("Could not load template")
        invalidresponse = escape_html("[development]")
        r = requests.get(url)
        self.assertEqual(r.status_code, 500)
        self.assertTrue(response in r.text)
        self.assertFalse(invalidresponse in r.text)

    def test_statictraversal(self):
        """Lets see if our text file is served correctly"""
        url = baseurl + "static/../config.ini"
        invalidresponse = escape_html("[development]")
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)
        self.assertFalse(invalidresponse in r.text)


class SmartClientTests(unittest.TestCase):
    """Test the 'smart' client functionality"""

    def test_get(self):
        """Lets see if the method route with GET returns valid content"""
        url = baseurl + "templateglobals"
        r = requests.get(url, headers={"Accept": "application/json"})
        self.assertEqual(r.encoding, "utf-8")

        with open(os.path.join(BASE_DIR, "templates/test.html"), "r") as template:
            templatehash = HashContent(template.read())

        returnvalue = (
            """{"template": "/test.html", "replacements": {"[header:part]": "path test", "[header:1:test:2]": "sparse path test", "[test]": "pagemaker return test", "[footer]": "&lt;b&gt;escaped html test&lt;/b&gt;"}, "template_hash": "%s"}"""
            % templatehash
        )

        self.assertEqual(r.status_code, 200)
        self.assertMultiLineEqual(returnvalue, r.text)

        templateurl = baseurl + "template/%s/%s" % (templatehash, "test.html")
        tr = requests.get(templateurl)
        self.assertEqual(tr.encoding, "utf-8")
        self.assertEqual(tr.status_code, 200)
        self.assertMultiLineEqual(templatehash, HashContent(tr.text))


if __name__ == "__main__":
    unittest.main()
