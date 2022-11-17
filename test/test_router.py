import unittest
from uweb3 import Router, App
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
        self.page_maker = DummyPageMaker()
        self.router = Router(self.page_maker)
        self.router.router(
            [
                ("/", "index", "GET"),
                ("/all", "all_methods"),
                ("/post", "post_only", "POST"),
                ("/only_digits/(\d+)/(\d+)", "route_args"),
                ("/any_route_args/(.*)/(.*)", "any_route_args"),
            ]
        )

    def get_data(self, router, args):
        handler, groups, hostmatch, page_maker = router(*args)
        return getattr(page_maker, handler)(*groups)

    def test_get_only_route(self):
        """Validate that a route is only accessible by the specified method(s)"""
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
            custom_router.router([("/", "index", method)])
            for m in [m for m in methods if m != method]:
                with self.assertRaises(NoRouteError):
                    self.get_data(custom_router, ("/", m, "*"))

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/", "POST", "*"))

    def test_methods_on_route(self):
        """Validate that a wildcard route is accessible by all methods."""
        for method in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"):
            assert "Hello from all methods" == self.get_data(
                self.router, ("/all", method, "*")
            )

    def test_tuple_allowed_methods(self):
        """Validate that routes with a tuple of allowed methods work."""
        custom_router = Router(self.page_maker)
        custom_router.router(
            [
                (
                    "/",
                    "index",
                    (
                        "POST",
                        "GET",
                    ),
                )
            ]
        )

        assert "Hello from index" == self.get_data(custom_router, ("/", "GET", "*"))
        assert "Hello from index" == self.get_data(custom_router, ("/", "POST", "*"))
        with self.assertRaises(NoRouteError):
            self.get_data(custom_router, ("/", "DELETE", "*"))

    def test_hostmatch(self):
        """Validate that a route is only accessible by the specified host(s)"""
        custom_router = Router(self.page_maker)
        custom_router.router(
            [
                (
                    "/",
                    "index",
                    (
                        "POST",
                        "GET",
                    ),
                    "127.0.0.1",
                )
            ]
        )
        assert "Hello from index" == self.get_data(
            custom_router, ("/", "GET", "127.0.0.1")
        )
        with self.assertRaises(NoRouteError):
            self.get_data(custom_router, ("/", "GET", "127.0.0.2"))

    def test_hostmatch_multiple_allowed_hosts(self):
        custom_router = Router(self.page_maker)
        custom_router.router(
            [
                (
                    "/",
                    "index",
                    (
                        "POST",
                        "GET",
                    ),
                    (
                        "127.0.0.1",
                        "127.0.0.2",
                    ),
                )
            ]
        )
        assert "Hello from index" == self.get_data(
            custom_router, ("/", "GET", "127.0.0.1")
        )
        assert "Hello from index" == self.get_data(
            custom_router, ("/", "GET", "127.0.0.2")
        )
        with self.assertRaises(NoRouteError):
            self.get_data(custom_router, ("/", "GET", "127.0.0.3"))

    def test_router_return_correct_variables(self):
        """Validate that the router returns the correct variables for each pattern."""

        for rgx, handler, method, hostmatch, *_ in self.router._req_routes:
            assert handler in (
                "index",
                "all_methods",
                "post_only",
                "route_args",
                "any_route_args",
            )
            assert method in ("GET", "POST", "ALL")
            assert hostmatch == "*"

        handler, groups, hostmatch, page_maker = self.router("/", "GET", "*")
        assert "index" == handler
        assert "*" == hostmatch
        assert type(self.page_maker) == type(page_maker)

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
                f"/any_route_args/{arg1}/{arg2}", "GET", "*"
            )
            assert [str(arg1), str(arg2)] == list(groups)


class RegisterAppRoutingTest(unittest.TestCase):
    def setUp(self):
        self.page_maker = DummyPageMaker()
        self.router = Router(self.page_maker)
        self.router.router(
            [
                ("/route_args/(\d+)/(\d+)", (DummyPageMaker, "route_args")),
                ("/alternative_routing", (DummyPageMaker, "alternative_routing")),
            ]
        )

    def get_data(self, router, args):
        handler, groups, hostmatch, page_maker = router(*args)
        return getattr(page_maker, handler)(page_maker, *groups)

    def test_register_route(self):
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_route", "GET", "*"))

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_post_only_route", "POST", "*"))

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
            self.router, ("/new_route", "GET", "*")
        )
        assert "Hello from new_post_only_route" == self.get_data(
            self.router, ("/new_post_only_route", "POST", "*")
        )

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_post_only_route", "GET", "*"))

    def test_register_app(self):
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_route", "GET", "*"))

        app = App(
            name="some app",
            routes=[("/new_route", (NewRoutingPageMaker, "index"), "GET", "*")],
        )
        self.router.register_app(app)
        assert "Hello from new routing index" == self.get_data(
            self.router, ("/new_route", "GET", "*")
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
            custom_router, ("/test/stringarg", "GET", "*")
        )
        assert ("123",) == self.get_data(custom_router, ("/test/123", "GET", "*"))

        with self.assertRaises(NoRouteError):
            self.get_data(custom_router, ("/test/@", "GET", "*"))


class AlternativeRoutingTest(unittest.TestCase):
    def setUp(self):
        self.page_maker = DummyPageMaker()
        self.router = Router(self.page_maker)
        self.router.router(
            [
                ("/", "index", "GET"),
                ("/post", "post_only", "POST"),
                ("/route_args/(\d+)/(\d+)", "route_args"),
                ("/alternative_routing", (DummyPageMaker, "alternative_routing")),
            ]
        )

    def get_data(self, router, args):
        handler, groups, hostmatch, page_maker = router(*args)
        return getattr(page_maker, handler)(page_maker, *groups)

    def test_alternative_routing(self):
        """Validate that routing  with the alternative syntax works.

        This tests the following:
            ("/route", (PageMaker, "RouteHandler")),
        """
        result = self.get_data(self.router, ("/alternative_routing", "GET", "*"))
        assert result == "Hello from alternative_routing"


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
