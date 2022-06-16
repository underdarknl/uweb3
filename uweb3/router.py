import re
from typing import NamedTuple
from .pagemaker import PageMaker


class NoRouteError(Exception):
    """The server does not know how to route this request"""


class RequestedRouteNotAllowed(NoRouteError):
    """"""


class App:
    def __init__(self, name, routes):
        self.name = name
        self.routes = routes


class RouteData(NamedTuple):
    pattern: re.Pattern
    handler: str
    method: str
    host: str
    page_maker: PageMaker


def route_method_allowed(routemethod, method):
    if routemethod != "ALL":
        if isinstance(routemethod, tuple) and method not in routemethod:
            raise RequestedRouteNotAllowed(
                "The requested method is not allowed on this route"
            )
        if not isinstance(routemethod, tuple) and method != routemethod:
            raise RequestedRouteNotAllowed(
                "The requested method is not allowed on this route"
            )


def match_host(hostpattern, host):
    hostmatch = None

    if hostpattern == "*":
        return "*"

    if isinstance(hostpattern, tuple):
        for pattern in hostpattern:
            try:
                return match_host(pattern, host)
            except RequestedRouteNotAllowed:
                continue
    else:
        hostmatch = re.compile(f"^{host}$").match(hostpattern)

    if not hostmatch:
        raise RequestedRouteNotAllowed(
            "The requested host is not allowed on this route"
        )
    hostmatch = hostmatch.group()
    return hostmatch


class Router:
    def __init__(self, page_class):
        self.page_class = page_class
        self._req_routes = []
        self._registered_apps = []

    def __call__(self, url, method, host):
        """Returns the appropriate handler and arguments for the given `url`.

        The`url` is matched against the compiled patterns in the `req_routes`
        provided by the outer scope. Upon finding a pattern that matches, the
        match groups from the regex and the unbound handler method are returned.

        N.B. The rules are such that the first matching route will be used. There
        is no further concept of specificity. Routes should be written with this in
        mind.

        Arguments:
            @ url: str
            The URL requested by the client.
            @ method: str
            The http method requested by the client.
            @ host: str
            The http host header value requested by the client.

        Raises:
            NoRouteError: None of the patterns match the requested `url`.

        Returns:
            2-tuple: handler method (unbound), and tuple of pattern matches.
        """
        for pattern, handler, routemethod, hostpattern, page_maker in self._req_routes:
            try:
                route_method_allowed(routemethod, method)
                hostmatch = match_host(hostpattern, host)
            except RequestedRouteNotAllowed:
                continue

            match = pattern.match(url)
            if match:
                # strip out optional groups, as they return '', which would override
                # the handlers default argument values later on in the page_maker
                groups = (group for group in match.groups() if group)
                return handler, groups, hostmatch, page_maker
        raise NoRouteError(url + " cannot be handled")

    def router(self, routes):
        """Returns the first request handler that matches the request URL.

        The `routes` argument is an iterable of 2-tuples, each of which contain a
        pattern (regex) and the name of the handler to use for matching requests.

        Before returning the closure, all regexp are compiled, and handler methods
        are retrieved from the provided `page_class`.

        Arguments:
            @ routes: iterable of 2-tuples.
            Each tuple is a pair of `pattern` and `handler`, both are strings.

        Returns:
            request_router: Configured closure that processes urls.
        """

        for pattern, handler, *details in routes:
            self.register_route(pattern, self.page_class, handler, details)

    def register_route(self, pattern, page_maker, handler, details):
        if not page_maker:
            raise NoRouteError(
                f"µWeb3 could not find a route handler called '{handler}' in any of the PageMakers, your application will not start."
            )
        method, host = self.extract_method_and_host(details)
        self._add_route(
            RouteData(
                pattern=re.compile(pattern + "$", re.UNICODE),
                handler=handler,
                method=method,
                host=host,
                page_maker=page_maker,
            )
        )

    def register_app(self, app: App):
        self._registered_apps.append(app)

        for route in app.routes:
            pattern, (page_maker, handler), *details = route
            method, host = self.extract_method_and_host(details)
            self._add_route(
                RouteData(
                    pattern=re.compile(pattern + "$", re.UNICODE),
                    handler=handler,
                    method=method,
                    host=host,
                    page_maker=page_maker,
                ),
                insert_at_start=True,
            )

    def _add_route(self, route: RouteData, insert_at_start: bool = False):
        if not insert_at_start:
            return self._req_routes.append(route)
        return self._req_routes.insert(0, route)

    def extract_method_and_host(self, details):
        METHODS = 0
        HOSTS = 1

        if len(details) and (
            isinstance(details[METHODS], tuple) or isinstance(details[METHODS], list)
        ):
            method = details[METHODS]
        else:
            method = details[METHODS].upper() if len(details) else "ALL"

        if len(details) > 1 and (
            isinstance(details[HOSTS], tuple) or isinstance(details[HOSTS], list)
        ):
            host = details[HOSTS]
        else:
            host = details[HOSTS].lower() if len(details) > 1 else "*"
        return method, host
