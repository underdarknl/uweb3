"""A minimal uWeb3 project scaffold."""
import os

# Third-party modules
import uweb3

# Application
from . import pages

__version__ = "0.1"


def main():
    """Creates a uWeb3 application.

    The application is created from the following components:

    - The presenter class (PageMaker) which implements the request handlers.
    - The routes iterable, where each 2-tuple defines a url-pattern and the
      name of a presenter method which should handle it.
    - The execution path, internally used to find templates etc.
    """
    return uweb3.uWeb(
        pages.PageMaker,
        [
            ("/", "Index"),
            ("/post", "Post"),
            ("/method", "Index", "GET"),
            ("/method", "Post", "POST"),
            ("/method", "Put", "PUT"),
            ("/method", "Delete", "DELETE"),
            ("/arguments/(\d+)/(\w+)/?(.*?)", "HtmlArgumentReflect"),
            ("/text/arguments/(\d+)/(\w+)/?(.*?)", "TextArgumentReflect"),
            ("/cookie/set", "Cookieset"),
            ("/cookie/set/secure", "Cookiesetsecure"),
            ("/cookie/reflect", "Cookiereflect"),
            ("/cookie/set/redirect", "CookiesetRedirect"),
            ("/cookie/set/templatedecorated", "TemplateDecoratedCookieset"),
            ("/signedcookie/set", "SignedCookieset"),
            ("/signedcookie/reflect", "SignedCookieReflect"),
            ("/templatedecorator", "TemplateDecorator"),
            ("/templateglobals", "TemplateGlobals"),
            ("/templatetraversal", "TemplateTraversal"),
            ("/sqlite/read/(.*)", "SqliteRead"),
            ("/mysql/read/(\d+)/?(.*)?", "MysqlRead"),
            ("/mysql/write", "MysqlWrite", "POST"),
            ("/jsonapi/read/(.*)", "JsonApiRead"),
            ("/redirect", "Redirect"),
            ("/static/(.*)", "Static"),
            ("/error", "ThrowError"),
            ("/none", "ReturnNone"),
            ("/emptystr", "ReturnEmptyStr"),
            ("/json", "ReturnJson"),
            ("/jsonstring", "ReturnJsonString"),
            ("/contenttypedecorator", "ReturnJsonDecorated"),
            ("/sparsetests", "SparseTests"),
            ("/sparseteststarget", "SparseTestsTarget"),
            ("/template/(\w+)/(.*?)", "SparseTemplateProvider"),
            ("/sparse.js", "SparseRenderedProvider"),
            ("/(.*)", "FourOhFour"),
        ],
        os.path.dirname(__file__),
    )
