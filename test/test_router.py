import unittest
from uweb3 import Router, App, RouteData, PageMaker
from uweb3 import NoRouteError


class DummyPageMaker:
    def index(self):
        return "Hello from index"

    def post_only(self):
        return "Hello from post_only"

    def new_route(self):
        return "Hello from new_route"

    def new_post_only_route(self):
        return "Hello from new_post_only_route"


class NewRoutingPageMaker:
    def index(self):
        return "Hello from new routing index"


class RouterTest(unittest.TestCase):
    def setUp(self):
        self.page_maker = DummyPageMaker()
        self.router = Router(self.page_maker)
        self.router.router([("/", "index", "GET"), ("/post", "post_only", "POST")])

    def get_data(self, router, args):
        handler, groups, hostmatch, page_maker = router(*args)
        return getattr(page_maker, handler)(*groups)

    def get_data_new_routing(self, router, args):
        handler, groups, hostmatch, page_maker = router(*args)
        return getattr(page_maker, handler)(page_maker, *groups)

    def test_basic_route(self):
        assert "Hello from index" == self.get_data(self.router, ("/", "GET", "*"))

    def test_default_wildcard(self):
        custom_router = Router(self.page_maker)
        custom_router.router([("/", "index"), ("/post", "post_only", "POST")])

        assert "Hello from index" == self.get_data(custom_router, ("/", "GET", "*"))
        assert "Hello from index" == self.get_data(custom_router, ("/", "POST", "*"))
        assert "Hello from index" == self.get_data(custom_router, ("/", "PUT", "*"))
        assert "Hello from index" == self.get_data(custom_router, ("/", "DELETE", "*"))
        assert "Hello from index" == self.get_data(custom_router, ("/", "OPTIONS", "*"))

    def test_post_only(self):
        assert "Hello from post_only" == self.get_data(
            self.router, ("/post", "POST", "*")
        )

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/post", "GET", "*"))

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/post", "DELETE", "*"))

    def test_register_route(self):
        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_route", "GET", "*"))

        with self.assertRaises(NoRouteError):
            self.get_data(self.router, ("/new_post_only_route", "POST", "*"))

        self.router.register_route("/new_route", self.page_maker, "new_route", ("GET",))
        self.router.register_route(
            "/new_post_only_route", self.page_maker, "new_post_only_route", ("POST",)
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
        app = App(
            name="some app",
            routes=[("/new_route", (NewRoutingPageMaker, "index"), "GET", "*")],
        )

        with self.assertRaises(NoRouteError):
            self.get_data_new_routing(self.router, ("/new_route", "GET", "*"))

        self.router.register_app(app)
        assert "Hello from new routing index" == self.get_data_new_routing(
            self.router, ("/new_route", "GET", "*")
        )

    def test_register_app_get_only_route(self):
        app = App(
            name="some app",
            routes=[("/new_route", (NewRoutingPageMaker, "index"), "GET", "*")],
        )
        self.router.register_app(app)

        with self.assertRaises(NoRouteError):
            self.get_data_new_routing(self.router, ("/new_route", "POST", "*"))

        with self.assertRaises(NoRouteError):
            self.get_data_new_routing(self.router, ("/new_route", "DELETE", "*"))


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
