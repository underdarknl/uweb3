import re
from typing import NamedTuple, Optional, Tuple, Union

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


class RouteArgs(NamedTuple):
    url: str
    methods: Union[str, Tuple[str, ...]]
    hostmatch: Optional[Tuple[str, ...]]


def register_pagemaker(cls):
    cls._routes = []
    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method, "_route_args"):
            if method._route_args.hostmatch:
                cls._routes.append(
                    (
                        method._route_args.url,
                        (cls, methodname),
                        method._route_args.methods,
                        method._route_args.hostmatch,
                    )
                )
            else:
                cls._routes.append(
                    (
                        method._route_args.url,
                        (cls, methodname),
                        method._route_args.methods,
                    )
                )
    return cls


def route(
    url: str,
    methods: Optional[Union[str, Tuple[str, ...]]] = "ALL",
    hostmatch: Optional[Tuple[str, ...]] = None,
):
    def wrapper(func):
        func._route_args = RouteArgs(url=url, methods=methods, hostmatch=hostmatch)
        return func

    return wrapper


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


def extract_method_and_host(details):
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


class Pattern:
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

    def __call__(self, url):
        return url.replace(self.name, self.pattern)


class PatternParser:
    def __init__(self):
        self._registered_patterns = {}
        self.add_default_patterns()

    def register_pattern(self, pattern: Pattern):
        self._registered_patterns[pattern.name] = pattern

    def add_default_patterns(self):
        self.register_pattern(Pattern(name="<int>", pattern="([0-9]+)"))
        self.register_pattern(Pattern(name="<str>", pattern="([a-zA-Z]+)"))
        self.register_pattern(Pattern(name="<alphanum>", pattern="([a-zA-Z0-9]+)"))

    def parse(self, url):
        for _, parser in self._registered_patterns.items():
            url = parser(url)
        return url


class Router:
    def __init__(self, page_class):
        self.page_class = page_class
        self._req_routes = []
        self._registered_apps = []
        self._parser = PatternParser()

    def __call__(self, url, method, host):
        """Calling the router will attempt to find the corresponding handler for the given url and method.

        This will take into account the host and method of the request, these values will be matched
        against the allowed values for the route. If either of the values do not pass the test, a
        RouteError will be raised.


        The`url` is matched against the compiled patterns in the registered routes list.
        Upon finding a pattern that matches, the match groups from the regex and the unbound handler method are returned.

        N.B. The rules are such that the first matching route will be used. There
        is no further concept of specificity. Routes should be written with this in
        mind. However when using the register_app method routes will be inserted at the start of the list
        to prevent matching the error handlers first, since these are present in the basepages class that is
        supplied at uweb3 initialization time.

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
            4-tuple: method (unbound) groups (method args), hostmatch, page_maker

            For example:
                ("index", ('argument1', 'argument2', ...), "*", basepages.PageMaker)
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
                if isinstance(handler, tuple):
                    page_maker = handler[0]
                    handler = handler[1]

                return handler, groups, hostmatch, page_maker
        raise NoRouteError(url + " cannot be handled")

    def router(self, routes):
        """Setup for the regular uweb3 router.

        This method adds the routes and its handler to a list of known routes.

        Before returning the closure, all regexp are compiled, and handler methods
        are retrieved from the provided `page_class`.

        Arguments:
            @ routes: iterable containing at least the pattern and handler.
                Optionally it can also containg a tuple of allowed methods, and a tuple of allowed hosts.

        Example:
            Basic usage:
                routes = (
                        "/", # The pattern to match
                        "index", # The handler that is present in the page_class supplied to the uweb3 constructor.
                    )
            Or:
                routes = (
                        "/", # The pattern to match
                        "index", # The handler that is present in the page_class supplied to the uweb3 constructor.
                        "GET", # The allowed method,
                        "127.0.0.1", # The allowed host,
                    )
            And lastely:
                routes = (
                        "/", # The pattern to match
                        "index", # The handler that is present in the page_class supplied to the uweb3 constructor.
                        (
                            "POST", # The tuple of allowed methods
                            "GET",
                        ),
                        (
                            "127.0.0.1", # The tuple of allowed hosts
                            "127.0.0.2",
                        ),
                    )
        """

        for pattern, handler, *details in routes:
            self.register_route(pattern, self.page_class, handler, details)

    def register_route(
        self, pattern: str, page_maker, handler: Union[str, tuple], details
    ):
        """Used to register a route to the tail of the list.

        Args:
            pattern (re.Pattern): The regex pattern to match when a request is coming in.
            page_maker (PageMaker): The unitialized page maker class.
            handler (str | tuple): The name of the handler (method) in the page_maker
                class. If this is a tuple it is assumed that the first element is the
                pagemaker class and the second element is the handler name.
                For example:
                    ("SomePageMaker", "handler_method")
            details (tuple): Containing the methods and hosts that are allowed for this route.

        Raises:
            NoRouteError: Raised when no PageMaker is passed.
        """
        if not page_maker:
            raise NoRouteError(
                f"µWeb3 could not find a route handler called '{handler}' in any of the PageMakers, your application will not start."
            )

        if isinstance(handler, tuple):
            page_maker = handler[0]
            handler = handler[1]

        pattern = self._parser.parse(pattern)
        method, host = extract_method_and_host(details)
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
        """Register a new app to the router.

        This app is inserted at the start of the list to prevent its routes from never
        being found. This is because the uweb3 class is initialized with the route
        handlers that are responsible for matching routes that are not existing.

        Args:
            app (uweb3.App): A uweb3 App object.
        """
        self._registered_apps.append(app)
        for route in app.routes:
            pattern, (page_maker, handler), *details = route
            pattern = self._parser.parse(pattern)
            method, host = extract_method_and_host(details)
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
        pattern, handler, routemethod, hostpattern, page_maker = route

        if not hasattr(page_maker, handler):
            raise NoRouteError(
                f"Could not find handler '{handler}' in pagemaker '{page_maker}'"
            )

        if not insert_at_start:
            return self._req_routes.append(route)
        return self._req_routes.insert(0, route)
