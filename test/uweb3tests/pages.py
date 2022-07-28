#!/usr/bin/python
"""Request handlers for the uWeb3 project scaffold"""
# standard modules
import json

# modules
import uweb3

# package imports
from . import model


class PageMaker(uweb3.DebuggingPageMaker, uweb3.SparseAsyncPages):
    """Holds all the request handlers for the application"""

    def _PostInit(self):
        """Register some vars to be used in the template parser later on"""
        self.parser.RegisterTag("header:part", "path test")
        self.parser.RegisterTag("header:1:test:2", "sparse path test")
        self.parser.RegisterTag("footer", "<b>escaped html test</b>")
        model.Fish.create_table(self.connection)
        model.Tank.create_table(self.connection)

    def Index(self):
        """Returns the index template"""
        return self.parser.Parse("index.html")

    def Post(self):
        """Returns the posted data as json"""
        return uweb3.Response(
            uweb3.JSONsafestring(json.dumps(self.post, cls=uweb3.JsonEncoder)),
            content_type="application/json",
        )

    def Put(self):
        """Returns the put data as text"""
        return uweb3.Response(
            self.put.getfirst("key", "invalid"), content_type="text/plain"
        )

    def Delete(self):
        """Returns the delete string as text"""
        return uweb3.Response("delete done", content_type="text/plain")

    def Cookieset(self):
        """Returns the index template and sets a cookie

        As cookies should not contain UTF8 we just use ascii."""
        self.req.AddCookie("example", "this is an example cookie value set by uWeb")
        return self.parser.Parse("index.html")

    def Cookiesetsecure(self):
        """Returns the index template and sets a cookie with a secure flag."""
        self.req.AddCookie(
            "example", "this is an example cookie value set by uWeb", secure=True
        )
        return self.parser.Parse("index.html")

    def Cookiereflect(self):
        """Returns the cookies value."""
        return self.cookies["cookie"]

    def CookiesetRedirect(self):
        """Returns to the index and sets a cookie"""
        self.req.AddCookie("example", "this is an example cookie value set by uWeb")
        return self.req.Redirect("/")

    def SignedCookieset(self):
        """Returns the index template and sets a signed cookie

        As signed cookies should not contain UTF8 we just use ascii."""
        data = "this is an example cookie value set by uWeb"
        model.SignedExample.Create(self.connection, {"key": data})
        return self.parser.Parse("index.html")

    def SignedCookieReflect(self):
        """Returns signed cookie if valid."""
        return model.SignedExample(self.connection)

    def HtmlArgumentReflect(self, numeric, string, optional="test"):
        """Returns the url arguments as parsed by the router."""
        return (numeric, string, optional)

    def TextArgumentReflect(self, numeric, string, optional="test"):
        """Returns the url arguments as parsed by the router."""
        return uweb3.Response((numeric, string, optional), content_type="text/plain")

    @uweb3.decorators.TemplateParser("index.html")
    def TemplateDecoratedCookieset(self):
        """Returns the index template and sets a cookie"""
        self.req.AddCookie("example", "this is an example cookie value set by uWeb")

    @uweb3.decorators.TemplateParser("index.html")
    def TemplateDecorator(self):
        """Returns the index template"""

    @uweb3.decorators.TemplateParser("test.html")
    def TemplateGlobals(self):
        """Returns the index template"""
        return {"test": "pagemaker return test"}

    @uweb3.decorators.TemplateParser("sparse.html")
    def SparseTests(self):
        """Returns the sparse template"""

    @uweb3.decorators.TemplateParser("sparse_target.html")
    def SparseTestsTarget(self):
        """Returns the sparse_target template"""

    @uweb3.decorators.TemplateParser("../config.ini")
    def TemplateTraversal(self):
        """Tries to load an invalid template by traversing up the tree"""
        return {"test": "pagemaker return test"}

    def Redirect(self):
        """Redirects to the homepage"""
        return uweb3.Redirect("/")

    def SqliteRead(self, fish=1):
        """Reads form the SQLite db"""
        try:
            return model.Fish.FromPrimary(self.connection, int(fish))
        except uweb3.model.NotExistError:
            return uweb3.Response(
                "No such fish", httpcode=404, content_type="text/plain"
            )

    def MysqlRead(self, tank=1, contenttype="html"):
        """Reads form the Mysql db"""
        try:
            record = model.Tank.FromPrimary(self.connection, int(tank))
            if contenttype != "html":
                return uweb3.Response(record, content_type=contenttype)
            return record
        except uweb3.model.NotExistError:
            return uweb3.Response(
                "No such tank", httpcode=404, content_type="text/plain"
            )

    def MysqlWrite(self):
        """Writes to the Mysql db"""
        newtank = model.Tank.Create(
            self.connection, {"name": self.post.getfirst("name", "Empty post")}
        )
        return newtank

    def JsonApiRead(self, post=1):
        """Reads form the Json API"""
        try:
            return model.Posts.FromPrimary(self.connection, int(post))
        except uweb3.model.NotExistError:
            return uweb3.Response(
                "No such post", httpcode=404, content_type="text/plain"
            )

    def ThrowError(self):
        """The request could not be fulfilled, this returns a 500."""
        raise Exception("error")

    def ReturnNone(self):
        """returns a Python None."""
        return None

    def ReturnEmptyStr(self):
        """returns a Python empty str."""
        return ""

    def ReturnJsonString(self):
        """Returns a string, escaped by the json handler to become a json safe tring instead."""
        return uweb3.Response(
            '{"message": "Hello, World!"}', content_type="application/json"
        )

    def ReturnJson(self):
        """Returns a json page"""
        return uweb3.Response(
            {"message": "Hello, World!"}, content_type="application/json"
        )

    @uweb3.decorators.ContentType("application/json")
    def ReturnJsonDecorated(self):
        """Returns a json page"""
        return {"message": "Hello, World!"}

    def FourOhFour(self, path):
        """The request could not be fulfilled, this returns a 404."""
        self.req.response.httpcode = 404
        return self.parser.Parse("404.html", path=path)
