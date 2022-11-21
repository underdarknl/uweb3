import unittest

from uweb3 import App, Router
from uweb3.router import NoRouteError


class DummyPageMaker:
    def index(self):
        return "Hello from index"

    def all_methods(self):
        return "Hello from all methods"

    def post_only(self):
        return "Hello from post_only"

    def any_route_args(self, *args):
        return args

    def route_args(self, *args):
        return args

    def route_args_int(self, *args):
        return args

    def alternative_routing(self):
        return "Hello from alternative_routing"


class TestPageMaker:
    """Test class for page maker"""


class NewRoutingPageMaker:
    def index(self):
        return "Hello from new routing index"

    def route_args(self, *args):
        return args

    def route_args_int(self, *args):
        return args

    def new_route(self):
        return "Hello from new_route"

    def new_post_only_route(self):
        return "Hello from new_post_only_route"


class DefaultRoutingTest(unittest.TestCase):
    def setUp(self):
        self.page_maker = DummyPageMaker
        self.router = Router(self.page_maker)
        self.router.router(
            [
                ("/", "index", "GET"),
                ("/all", "all_methods"),
                ("/post", "post_only", "POST"),
                ("/only_digits/(\d+)/(\d+)", "route_args"),
                ("/any_route_args/(.*)/(.*)", "any_route_args"),
                ("/test_tuple_methods", "index", ("POST", "GET")),
                ("/test_hostmatch", "index", ("POST", "GET"), "127.0.0.1"),
                (
                    "/test_tuple_hostmatch",
                    "index",
                    ("POST", "GET"),
                    ("127.0.0.1", "127.0.0.2"),
                ),
            ]
        )

    def get_data(self, router, args, host="127.0.0.1"):
        handler, groups, hostmatch, page_maker = router(*args, host)
        return getattr(page_maker, handler)(page_maker, *groups)

    def test_specified_method_on_route(self, handler="index"):
        """Validate that a route is only accessible by the specified method(s).

        Args:
            Handler (str): The name of the handler to test.
                This can be overwritten in subclasses to test other handlers.
        """

        methods = (
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "HEAD",
            "OPTIONS",
            ("Z",),
            ("X", "Y"),
        )
        for method in methods:
            custom_router = Router(self.page_maker)
            custom_router.router([("/", handler, method)])
            for m in [m for m in methods if m != method]:
                with self.assertRaises(NoRouteError):
                    self.get_data(custom_router, ("/", m))

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/", "POST"))

    def test_methods_on_route(self):
        """Validate that a wildcard route is accessible by all methods."""
        for method in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"):
            assert "Hello from all methods" == self.get_data(
                self.router, ("/all", method)
            )

    def test_tuple_allowed_methods(self):
        """Validate that routes with a tuple of allowed methods work."""

        assert "Hello from index" == self.get_data(
            self.router, ("/test_tuple_methods", "GET")
        )
        assert "Hello from index" == self.get_data(
            self.router, ("/test_tuple_methods", "POST")
        )
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/", "DELETE"))

    def test_hostmatch(self):
        """Validate that a route is only accessible by the specified host(s)"""

        assert "Hello from index" == self.get_data(
            self.router, ("/test_hostmatch", "GET"), host="127.0.0.1"
        )
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/test_hostmatch", "GET"), host="127.0.0.2")

    def test_hostmatch_multiple_allowed_hosts(self):

        assert "Hello from index" == self.get_data(
            self.router, ("/test_tuple_hostmatch", "GET"), host="127.0.0.1"
        )
        assert "Hello from index" == self.get_data(
            self.router, ("/test_tuple_hostmatch", "GET"), host="127.0.0.2"
        )
        with self.assertRaises(NoRouteError):
            self.get_data(
                self.router, ("/test_tuple_hostmatch", "GET"), host="127.0.0.3"
            )

    def test_router_return_correct_variables(self):
        """Validate that the router returns the correct variables for each pattern."""

        for rgx, handler, method, hostmatch, page_maker, *_ in self.router._req_routes:
            assert handler in (
                "index",
                "all_methods",
                "post_only",
                "route_args",
                "any_route_args",
            )
            assert method in ("GET", "POST", "ALL", ("POST", "GET"))

    def test_route_args(self):
        """Validate that route arguments are passed to the handler."""
        args = [
            (1, 2),
            ("string_arg", "string_arg2"),
            ("arg1", 2),
            (1.23, 4.56),
            ("str", "alphanum123"),
        ]

        for arg1, arg2 in args:
            handler, groups, hostmatch, page_maker = self.router(
                f"/any_route_args/{arg1}/{arg2}", "GET", host="127.0.0.1"
            )
            assert [str(arg1), str(arg2)] == list(groups)


class AlternativeRoutingTest(DefaultRoutingTest):
    def setUp(self):
        self.page_maker = TestPageMaker()
        self.router = Router(self.page_maker)
        self.router.router(
            [
                ("/", (DummyPageMaker, "index"), "GET"),
                ("/all", (DummyPageMaker, "all_methods")),
                ("/post", (DummyPageMaker, "post_only"), "POST"),
                ("/only_digits/(\d+)/(\d+)", (DummyPageMaker, "route_args")),
                ("/any_route_args/(.*)/(.*)", (DummyPageMaker, "any_route_args")),
                ("/test_tuple_methods", (DummyPageMaker, "index"), ("POST", "GET")),
                (
                    "/test_hostmatch",
                    (DummyPageMaker, "index"),
                    ("POST", "GET"),
                    "127.0.0.1",
                ),
                (
                    "/test_tuple_hostmatch",
                    (DummyPageMaker, "index"),
                    ("POST", "GET"),
                    ("127.0.0.1", "127.0.0.2"),
                ),
            ]
        )

    def test_specified_method_on_route(self, handler=(DummyPageMaker, "index")):
        """Overwrite the test to use a tuple for the handler.
        This test validates that specific method only routes also work in this way
        of routing.
        """
        super().test_specified_method_on_route(handler)


class RegisterAppRoutingTest(DefaultRoutingTest):
    def setUp(self):
        self.page_maker = DummyPageMaker()
        self.router = Router(self.page_maker)
        self.router.router(
            [
                ("/", (DummyPageMaker, "index"), "GET"),
                ("/all", (DummyPageMaker, "all_methods")),
                ("/post", (DummyPageMaker, "post_only"), "POST"),
                ("/only_digits/(\d+)/(\d+)", (DummyPageMaker, "route_args")),
                ("/any_route_args/(.*)/(.*)", (DummyPageMaker, "any_route_args")),
                ("/test_tuple_methods", (DummyPageMaker, "index"), ("POST", "GET")),
                (
                    "/test_hostmatch",
                    (DummyPageMaker, "index"),
                    ("POST", "GET"),
                    "127.0.0.1",
                ),
                (
                    "/test_tuple_hostmatch",
                    (DummyPageMaker, "index"),
                    ("POST", "GET"),
                    ("127.0.0.1", "127.0.0.2"),
                ),
            ]
        )

    def test_register_route(self):
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_route", "GET"))

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_post_only_route", "POST"))

        self.router.register_route(
            "/new_route", NewRoutingPageMaker, "new_route", ("GET",)
        )
        self.router.register_route(
            "/new_post_only_route",
            NewRoutingPageMaker,
            "new_post_only_route",
            ("POST",),
        )

        assert "Hello from new_route" == self.get_data(
            self.router, ("/new_route", "GET")
        )
        assert "Hello from new_post_only_route" == self.get_data(
            self.router, ("/new_post_only_route", "POST")
        )

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_post_only_route", "GET"))

    def test_register_app(self):
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_route", "GET"))

        app = App(
            name="some app",
            routes=[("/new_route", (NewRoutingPageMaker, "index"), "GET")],
        )
        self.router.register_app(app)
        assert "Hello from new routing index" == self.get_data(
            self.router, ("/new_route", "GET")
        )

    def test_pattern_routing(self):
        custom_router = Router(self.page_maker)
        custom_router.router(
            [
                (
                    "/test/<str>",
                    (DummyPageMaker, "route_args"),
                ),
                (
                    "/test/<int>",
                    (DummyPageMaker, "route_args_int"),
                ),
            ]
        )
        assert ("stringarg",) == self.get_data(
            custom_router, ("/test/stringarg", "GET")
        )
        assert ("123",) == self.get_data(custom_router, ("/test/123", "GET"))

        with self.assertRaises(NoRouteError):
            self.get_data(custom_router, ("/test/@", "GET"))


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
