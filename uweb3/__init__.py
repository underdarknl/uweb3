#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""µWeb3 Framework"""

__version__ = "3.0.7"

# Standard modules
import datetime
import logging
import os
import sys
import time
from importlib import reload
from wsgiref.simple_server import make_server

# Package modules
from . import pagemaker, request
from .libs import sqltalk
from .libs.safestring import Basesafestring, HTMLsafestring, JsonEncoder, JSONsafestring
from .model import SettingsManager
from .pagemaker import (
    DebuggingPageMaker,
    LoginMixin,
    PageMaker,
    SparseAsyncPages,
    decorators,
)

# Package classes
from .response import Redirect, Response
from .router import (
    App,
    NoRouteError,
    RequestedRouteNotAllowed,
    RouteData,
    Router,
    register_pagemaker,
    route,
)


class Error(Exception):
    """Superclass used for inheritance and external exception handling."""


class ImmediateResponse(Exception):
    """Used to trigger an immediate response, foregoing the regular returns."""


class HTTPException(Error):
    """SuperClass for HTTP exceptions."""


class HTTPRequestException(HTTPException):
    """Exception for http request errors."""


class uWeb:
    """Returns a configured closure for handling page requests.

    This closure is configured with a precomputed set of routes and handlers using
    the Router function. After this, incoming requests are processed and delegated
    to the correct PageMaker handler.

    The url in the received `req` object is taken and matches against the
    `router`` (refer to Router() for more documentation on this).


    Takes:
      @ page_class: PageMaker
        Class that holds request handling methods as defined in the `routes`
      @ router: request router
        The result of the Router() function.
      @ config: dict
        Configuration for the PageMaker. Typically contains entries for database
        connections, default search paths etc.

    Returns:
      RequestHandler: Configured closure that is ready to process requests.
    """

    def __init__(self, page_class, routes, executing_path=None, config="config"):
        self.executing_path = executing_path or os.path.dirname(__file__)
        self.config = SettingsManager(filename=config, path=self.executing_path)
        self._accesslogger = None
        self._errorlogger = None
        self.initial_pagemaker = page_class
        self.router = Router(page_class)
        self.router.router(routes)
        self.encoders = {
            "text/html": lambda x: HTMLsafestring(x, unsafe=True),
            "text/plain": str,
            "text/csv": str,
            "application/json": lambda x: JSONsafestring(x, unsafe=True),
            "application/xml": lambda x: HTMLsafestring(x, unsafe=True),
            "default": bytes,
        }

        accesslogging = (
            self.config.options.get("log", {}).get("access_logging", True) != "False"
        )
        self._logrequest = self.logrequest if accesslogging else lambda *args: None
        # log exceptions even when development is present, but error_logging was not disabled specifically
        errorlogging = (
            self.config.options.get("log", {"error_logging": "False"}).get(
                "error_logging", "True"
            )
            == "True"
        )
        self._logerror = self.logerror if errorlogging else lambda *args: None

    def _create_request(self, env):
        """Creates the request.Request object with all required parameters.

        Args:
            env (wsgi Environment): The WSGI environment dictionary
        Returns:
            request (request.Request): Uweb3 Request object.
        """
        max_request_body_size = None
        remote_addr_config = None

        # Attempt to load the max request size setting from the config
        try:
            max_request_body_size = self.config.options["general"][
                "max_request_body_size"
            ]
        except Exception:
            pass

        try:
            remote_addr_config = self.config.options["headers"]
        except Exception:
            pass

        if max_request_body_size:
            return request.Request(
                env,
                self.logger,
                self.errorlogger,
                max_request_body_size=max_request_body_size,
                remote_addr_config=remote_addr_config,
            )
        return request.Request(
            env,
            self.logger,
            self.errorlogger,
            remote_addr_config=remote_addr_config,
        )

    def __call__(self, env, start_response):  # noqa: C901
        """WSGI request handler.
        Accepts the WSGI `environment` dictionary and a function to start the
        response and returns a response iterator.
        """
        req = self._create_request(env)

        try:
            req.process_request()
        except request.HeaderError as exc:
            self.log_request_error(req)
            pagemaker_instance = PageMaker(
                req, config=self.config, executing_path=self.executing_path
            )
            response = pagemaker_instance.BadRequest(str(exc))
            return self._finish_response(response, req, start_response)

        response = None
        method = "_NotFound"
        args = None

        try:
            method, args, hostargs, page_maker = self.router(
                req.path, req.env["REQUEST_METHOD"], req.env["REAL_REMOTE_ADDR"]
            )
        except NoRouteError:
            # When we catch this error this means there is no method for the route in the currently selected pagemaker.
            # If this happens we default to the initial pagemaker because we don't know what the target pagemaker should be.
            # Then we set an internalservererror and move on
            page_maker = self.initial_pagemaker

        try:
            # instantiate the pagemaker for this request
            pagemaker_instance = page_maker(
                req, config=self.config, executing_path=self.executing_path
            )
            # specifically call _PreRequest as promised in documentation
            if hasattr(pagemaker_instance, "_PreRequest"):
                try:
                    # we handle the preRequest seperately because otherwise we cannot show debugging info
                    pagemaker_instance = (
                        pagemaker_instance._PreRequest() or pagemaker_instance
                    )
                except Exception:
                    # lets use the intended pagemaker, but skip prerequest as it crashes, this enabled rich debugging info if enabled.
                    response = pagemaker_instance.InternalServerError(*sys.exc_info())
            if not response:
                response = self.get_response(req, pagemaker_instance, method, args)
        except Exception:
            # something broke in our pagemaker_instance, lets fall back to the most basic pagemaker for error output
            if hasattr(pagemaker_instance, "_ConnectionRollback"):
                try:
                    pagemaker_instance._ConnectionRollback()
                except Exception:
                    pass
            pagemaker_instance = PageMaker(
                req, config=self.config, executing_path=self.executing_path
            )
            response = pagemaker_instance.InternalServerError(*sys.exc_info())

        static = method == "Static"

        if not static:
            if not isinstance(response, Response):
                req.response.text = response
                response = req.response

            if req.noparse:
                response.content_type = "application/json"

            if not isinstance(response.text, Basesafestring):
                # make sure we always output Safe Strings for our known content-types
                clean_content_type = response.clean_content_type()
                encoder = self.encoders.get(
                    clean_content_type,
                    self.encoders["application/xml"]
                    if str(clean_content_type).endswith("xml")
                    else self.encoders["default"],
                )
                response.text = encoder(response.text)

        # CSP might be unneeded for some static content,
        # https://github.com/w3c/webappsec/issues/520
        if hasattr(pagemaker_instance, "_CSPheaders"):
            pagemaker_instance._CSPheaders()

        # provide users with a PostRequest method to overide too
        if not static and hasattr(pagemaker_instance, "_PostRequest"):
            response = pagemaker_instance._PostRequest(response) or response
        pagemaker_instance.CloseRequestConnections()

        return self._finish_response(response, req, start_response)

    def _finish_response(self, response, req, start_response):
        # we should at least send out something to make sure we are wsgi compliant.
        if not response.text:
            response.text = ""

        self._logrequest(req, response)
        # XXX: PEP 3333 says we should check for errors in headers
        start_response(response.status, response.headerlist)
        try:
            yield response.text.encode(response.charset)
        except AttributeError:
            yield response.text

    @property
    def logger(self):
        if not self._accesslogger:
            logger = logging.getLogger("uweb3_logger")
            logger.setLevel(logging.INFO)
            logpath = os.path.join(
                self.executing_path,
                self.config.options.get("log", {}).get("acces_log", "access_log.log"),
            )

            delay = bool(
                self.config.options.get("log", {}).get("acces_log_delay", False)
            )

            encoding = self.config.options.get("log", {}).get(
                "acces_log_encoding", None
            )
            fh = logging.FileHandler(logpath, encoding=encoding, delay=delay)
            fh.setLevel(logging.INFO)
            logger.addHandler(fh)
            self._accesslogger = logger
        return self._accesslogger

    @property
    def errorlogger(self):
        if not self._errorlogger:
            logger = logging.getLogger("uweb3_exception_logger")
            logger.setLevel(logging.ERROR)
            logpath = os.path.join(
                self.executing_path,
                self.config.options.get("log", {}).get(
                    "exception_log", "uweb3_exceptions.log"
                ),
            )
            delay = bool(
                self.config.options.get("log", {}).get("exception_log_delay", False)
            )
            encoding = self.config.options.get("log", {}).get(
                "exception_log_encoding", None
            )
            fh = logging.FileHandler(logpath, encoding=encoding, delay=delay)
            fh.setLevel(logging.INFO)
            logger.addHandler(fh)
            self._errorlogger = logger
        return self._errorlogger

    def logrequest(self, req, response):
        """Logs incoming requests to the logfile."""
        host = req.env["HTTP_HOST"].split(":")[0]
        date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        method = req.method
        path = req.path
        get = req.vars["get"]
        status = response.httpcode
        protocol = req.env.get("SERVER_PROTOCOL")
        if not response.log:
            return self.logger.info(
                """%s - - [%s] \"%s %s %s %s %s\"""",
                host,
                date,
                method,
                path,
                get,
                status,
                protocol,
            )
        data = response.log
        return self.logger.info(
            """%s - - [%s] \"%s %s %s %s %s %s\"""",
            host,
            date,
            method,
            path,
            get,
            status,
            protocol,
            data,
        )

    def log_request_error(self, req):
        host = req.env["HTTP_HOST"].split(":")[0]
        date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        path = req.path
        protocol = req.env.get("SERVER_PROTOCOL")
        return self.errorlogger.exception(
            """%s - - [%s] \"%s %s\"""", host, date, path, protocol
        )

    def logerror(self, req, page_maker, pythonmethod, args):
        """Logs errors and exceptions to the logfile."""
        host = req.env["HTTP_HOST"].split(":")[0]
        date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        method = req.method
        path = req.path
        protocol = req.env.get("SERVER_PROTOCOL")
        args = [str(arg) for arg in args]
        return self.errorlogger.exception(
            """%s - - [%s] \"%s %s %s %s.%s(%s)\"""",
            host,
            date,
            method,
            path,
            protocol,
            page_maker,
            pythonmethod,
            args,
        )

    def get_response(self, req, page_maker, method, args):
        try:
            if method != "Static":
                # We're specifically calling _PostInit here as promised in documentation.
                # pylint: disable=W0212
                page_maker._PostInit()
            elif hasattr(page_maker, "_StaticPostInit"):
                # We're specifically calling _StaticPostInit here as promised in documentation, seperate from the regular PostInit to keep things fast for static pages
                page_maker._StaticPostInit()

            # pylint: enable=W0212
            return getattr(page_maker, method)(*args)
        except pagemaker.ReloadModules as message:
            reload_message = reload(sys.modules[self.initial_pagemaker.__module__])
            return Response(content="%s\n%s" % (message, reload_message))
        except ImmediateResponse as err:
            return err[0]
        except Exception:
            self._logerror(req, page_maker, method, args)
            return page_maker.InternalServerError(*sys.exc_info())

    def serve(self):
        """Sets up and starts WSGI development server for the current app."""
        host = "localhost"
        port = 8001
        hotreload = False
        interval = None

        if self.config.options.get("development", False):
            devconfig = self.config.options["development"]
            host = devconfig.get("host", host)
            port = devconfig.get("port", port)
            hotreload = devconfig.get("reload", False) in ("True", "true")

        server = make_server(host, int(port), self)
        print(
            f"Running µWeb3 server on http://{server.server_address[0]}:{server.server_address[1]}"
        )
        print(f"Root dir is: {self.executing_path}")
        if hotreload:
            ignored_directories = [
                "__pycache__",
                self.initial_pagemaker.PUBLIC_DIR,
                self.initial_pagemaker.TEMPLATE_DIR,
            ]
            ignored_extensions = []
            interval = int(devconfig.get("checkinterval", 0))
            if "ignored_extensions" in devconfig:
                ignored_extensions = devconfig.get("ignored_extensions", "").split(",")
            if "ignored_directories" in devconfig:
                ignored_directories += devconfig.get("ignored_directories", "").split(
                    ","
                )

            print(f"Hot reload is enabled for changes in: {self.executing_path}")
            HotReload(
                self.executing_path,
                interval=interval,
                ignored_extensions=ignored_extensions,
                ignored_directories=ignored_directories,
            )
        try:
            server.serve_forever()
        except Exception as error:
            print(error)
            server.shutdown()

    def register_app(self, app: App):
        self.router.register_app(app)


class HotReload:
    """This class handles the thread which scans for file changes in the
    execution path and restarts the server if needed"""

    IGNOREDEXTENSIONS = [".pyc", ".ini", ".md", ".html", ".log", ".sql"]

    def __init__(
        self, path, interval=1, ignored_extensions=None, ignored_directories=None
    ):
        """Takes a path, an optional interval in seconds and an optional flag
        signaling a development environment which will set the path for new and
        changed file checking on the parent folder of the serving file."""
        import threading

        self.running = threading.Event()
        self.interval = interval
        self.path = os.path.dirname(path)
        self.ignoredextensions = self.IGNOREDEXTENSIONS + (ignored_extensions or [])
        self.ignoreddirectories = ignored_directories
        self.thread = threading.Thread(target=self.Run, daemon=True)
        self.thread.start()

    def Run(self):
        """Method runs forever and watches all files in the project folder."""
        self.watched_files = self.Files()
        self.mtimes = [(f, os.path.getmtime(f)) for f in self.watched_files]

        while True:
            time.sleep(self.interval)
            new = self.Files(self.watched_files)
            if new:
                print(
                    "{color}New file added or deleted\x1b[0m \nRestarting µWeb3".format(
                        color="\x1b[7;30;41m"
                    )
                )
                self.Restart()
            for f, mtime in self.mtimes:
                if os.path.getmtime(f) != mtime:
                    print(
                        "{color}Detected changes in {file}\x1b[0m \nRestarting µWeb3".format(
                            color="\x1b[7;30;41m", file=f
                        )
                    )
                    self.Restart()

    def Files(self, current=None):
        """Returns all files inside the working directory of µWeb3."""
        if not current:
            current = set()
        new = set()
        for dirpath, dirnames, filenames in os.walk(self.path):
            if any(
                list(map(lambda dirname: dirname in dirpath, self.ignoreddirectories))
            ):
                continue
            for file in filenames:
                fullname = os.path.join(dirpath, file)
                if fullname in current or fullname.endswith("~"):
                    continue
                ext = os.path.splitext(file)[1]
                if ext not in self.ignoredextensions:
                    new.add(fullname)
        return new

    def Restart(self):
        """Restart µWeb3 with all provided system arguments."""
        self.running.clear()
        os.execl(sys.executable, sys.executable, *sys.argv)
