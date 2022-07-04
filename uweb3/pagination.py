from abc import ABC, abstractmethod, abstractproperty
import math
from numbers import Number
import os
from operator import attrgetter, itemgetter
from typing import Callable, Iterable, List, Union
from uweb3.pagemaker import IndexedFieldStorage
from uweb3.templateparser import Parser


class PaginationError(Exception):
    pass


class NoPageError(PaginationError):
    pass


class InvalidPageNumber(PaginationError):
    pass


class PageNumberOutOfRange(PaginationError):
    pass


class InvalidSortArgument(PaginationError):
    pass


def _chunkify(iterable: Iterable, size: int) -> Iterable:
    """Yield successive chunks from iterable of length size."""
    items = list(iterable)
    for i in range(0, len(items), size):
        yield Page(i, items[i : i + size])


def sort_data(data, order, key):
    obj = list(data)
    if order == "ASC":
        obj.sort(
            key=itemgetter(key),
            reverse=False,
        )
    else:
        obj.sort(key=itemgetter(key), reverse=True)
    return obj


def to_page_number(requested_number):
    """Convert a request page number to an actual number.
    Invalid values will be replaced with 1 to redirect
    the user to the first page of the paginator object.

    Args:
        requested_number (str|Number): A string or Number
            representing the requested page number.

    Returns:
        int: The number of the requested page.
    """
    try:
        requested_number = int(requested_number)
    except Exception:
        requested_number = 1
    return requested_number if int(requested_number) > 1 else 1


class Page:
    def __init__(self, number: int, content: list):
        self.page_number = number
        self.content = content

    @property
    def items(self):
        return self.content

    def __iter__(self):
        return iter(self.content)

    def __len__(self):
        return len(self.content)


class Base:
    def __init__(
        self,
        get_req_dict: Union[IndexedFieldStorage, None] = None,
        page_size=10,
    ):
        """Base class for Paginators

        Args:
            get_req_dict (Union[IndexedFieldStorage, None], optional):
                IndexedFieldStorage present in PageMaker.req.
                This is used to determine page and sorting/ordering.
            page_size (int, optional): Determines how many items are
                allowed before creating a new page.
        """
        self._parser = Parser(
            path=os.path.join(os.path.dirname(__file__), "templates"),
            templates=("simple_pagination.html",),
        )
        self.page_size = page_size
        self.total_pages = 1
        self._page_number = 1
        self.get_data = get_req_dict
        self._pages = []

    @property
    def pages(self) -> List[Page]:
        """The list containg Page objects."""
        return self._pages

    @pages.setter
    def pages(self, value):
        """Setter method for the list of Pages.

        When populating the list of pages also calculate the
        amount of total pages present"""
        self._pages = value
        self.total_pages = len(self._pages)

    @property
    def current_page(self) -> Page:
        """Return the Page object with the items for the current page"""
        if not self.pages:
            raise NoPageError(f"No page for page number {self.page_number}")
        return self.pages[self.page_number - 1]

    @property
    def page_number(self) -> int:
        """Return the number of the currently displayed page"""
        return self._page_number

    @page_number.setter
    def page_number(self, value: Union[str, int]):
        """Attempt to set the value of the page that should be displayed.

        Args:
            value (str|int): The number of the page that should be
                displayed to the user. This value can be any format
                that can be converted to an int, but really only integers
                should be used to indicate a page.
        Raises:
            InvalidPageNumber: When the passed value could not be converted
                to an int succesfully.
        """
        if isinstance(value, int):
            if (value > self.total_pages) and self.total_pages >= 1:
                raise PageNumberOutOfRange("Page number is out of range")
            self._page_number = value
        elif isinstance(value, str) and value.isnumeric():
            self.page_number = int(value)
        else:
            # Should not be reached when calling to_page_number
            # method on request page number.
            # Instead the user will be redirected to page_number 1
            raise InvalidPageNumber("Page number is of an invalid type")

    @property
    def next_page(self):
        """Returns the number of the next page if possible, if this page
        is the last page return the current page number instead."""
        if self.page_number < self.total_pages:
            return self.page_number + 1
        else:
            return self.page_number

    @property
    def previous_page(self):
        """Returns the previous page number, if the current page is the first
        page already return the current page (1)."""
        if self.page_number > 1:
            return self.page_number - 1
        else:
            return self.page_number

    @property
    def render_nav(self):
        """Render navigation buttons for the Paginatior class.
        To render as intended use css.underdark.nl"""
        return self._parser.Parse(
            "simple_pagination.html",
            __paginator=self,
            __ranges=self._determine_page_numbers(),
            __query_url=self._query_url(),
        )

    def _query_url(self):
        """Add all required keys to the redirect url of a navigation element."""
        if not self.get_data:
            return ""

        return "".join(
            [
                f"&{key}={self.get_data.getfirst(key)}"
                for key in self.relevant_keys()
                if self.get_data.getfirst(key)
            ]
        )

    def relevant_keys(self):
        """List of relevant keys for paginator class.
        These are the keys that are allowed on a navigation element.

        Overwrite this method to indicate which keys are allowed."""
        return []

    def _determine_page_numbers(self):
        """Determine which numbers should be shown to the user depending
        on current page and total pages."""
        nav_end = min(self.previous_page + 4, self.total_pages + 1)
        if self.total_pages - self.page_number < 2:
            return range(max(1, self.previous_page - 2), nav_end)
        return range(self.previous_page, nav_end)

    def __iter__(self):
        return iter(self.pages)


class BasePagination(Base):
    def __init__(
        self,
        data: Iterable,
        *args,
        get_req_dict: Union[IndexedFieldStorage, None] = None,
        **kwargs,
    ):
        """Simple pagination class for dumping short list objects
        to a page with pagination options. This class should not be
        used to render thousands of database objects as there is a dedicated
        paginator class that uses offsets and limits to accomplish fast load times.

        Args:
            get_req_dict (Union[IndexedFieldStorage, None], optional):
                IndexedFieldStorage present in PageMaker.req.
                This is used to determine page and sorting/ordering.
            page_size (int, optional): Determines how many items are
                allowed before creating a new page.
        """
        super().__init__(*args, get_req_dict=get_req_dict, **kwargs)
        self.pages = list(_chunkify(data, self.page_size))

        if self.get_data and self.get_data.getfirst("page"):
            self.page_number = to_page_number(self.get_data.getfirst("page"))


class SortableBase(BasePagination):
    def __init__(
        self,
        data: Iterable,
        columns: tuple,
        get_req_dict: IndexedFieldStorage,
        *args,
        **kwargs,
    ):
        self.order = get_req_dict.getfirst("order", "ASC")
        self.sort = get_req_dict.getfirst("sort")
        self.columns = columns
        data = self.sort_data(data)
        super().__init__(data=data, *args, get_req_dict=get_req_dict, **kwargs)

    def sort_data(self, data: Iterable) -> Union[Iterable, list]:
        return NotImplemented

    @property
    def render_sortable_head(self):
        """Used to render the table head based on the supplied columns."""
        return self._parser.Parse(
            "sortable_table_head.html",
            __paginator=self,
        )

    @property
    def render_table(self):
        """Render the complete table based on the supplied columns and the
        provided data."""
        return self._parser.Parse(
            "simple_table.html",
            __paginator=self,
            __ranges=self._determine_page_numbers(),
            __query_url=self._query_url(),
        )


class SortablePagination(SortableBase):
    def sort_data(self, data: Iterable) -> Union[Iterable, list]:
        if self.sort and self.sort not in self.columns:
            raise InvalidSortArgument(
                f"Page was sorted on an invalid key {self.sort!r}"
            )

        if self.sort:
            return sort_data(data, self.order, self.sort)
        return data

    def relevant_keys(self):
        keys = super().relevant_keys()
        return keys + ["sort", "order"]


class OffsetPagination(Base):
    def __init__(
        self,
        method: Callable,
        *args,
        get_req_dict: Union[IndexedFieldStorage, None] = None,
        modelargs,
        **kwargs,
    ):
        """Paginator class used for pagination with model classes.
        This paginator was created with the model.Record.List method in mind.

        For successful use of this class the provided method should implement the
        following parameters: connection, limit, offset, yield_unlimited_total_first.
        By default this class is compatible with any uweb3 model.Record class as these come with the
        List function by default.

        yield_unlimited_total_first is used to determine the total amount of pages.
        If you want to use a custom method for populating this class the data
        supplied should look like this:
            generator(
                total_amount_of_items,
                {item1: value, ...},
                {item2: value, ...},
                ...
            ).
        
        args:
            method (Callable): A callable function used to retrieve the data from.
                read above for more information.
            get_req_dict (Union[IndexedFieldStorage, None], optional):
                IndexedFieldStorage present in PageMaker.req.
                This is used to determine page and sorting/ordering.
            modelargs: The arguments that should be supplied to your
                callable method. This should be a dictionary that can be 
                unpacked, and should at least contain the connection 
                parameter (when using model methods). 
                It is also possible to overwrite limit and offset, however
                this is not advisable as the paginator class uses these values.
                Any other parameters can be passed as long as your callable method
                has support for this.
        """
        super().__init__(get_req_dict, *args, **kwargs)
        self.requested_page = 1
        if self.get_data and self.get_data.getfirst("page"):
            # We cannot set self.page_number here because we need
            # to determine the total amount of pages first.
            self.requested_page = to_page_number(self.get_data.getfirst("page"))

        self.modelargs = modelargs
        self.method = method
        self._setup()

    def _setup(self):
        limit = self.page_size

        if "limit" in self.modelargs:
            offset = self.modelargs["limit"] * (self.requested_page - 1)
            limit = self.modelargs["limit"]
            self.modelargs.pop("limit")
        else:
            offset = self.page_size * (self.requested_page - 1)

        self.pages = self.method(
            offset=offset,
            limit=limit,
            yield_unlimited_total_first=True,
            **self.modelargs,
        )
        self.page_number = self.requested_page

    @property
    def current_page(self):
        return self.pages[0]

    @property
    def pages(self):
        return self._pages

    @pages.setter
    def pages(self, value):
        itemcount = next(value)
        self._pages = [Page(self.requested_page, list(value))]
        self.total_pages = int(math.ceil(float(itemcount) / self.page_size))
