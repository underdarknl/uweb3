from abc import ABC, abstractmethod, abstractproperty
import math
import os
from operator import attrgetter, itemgetter
from typing import Callable, Iterable, Union
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


class Page:
    def __init__(self, number: int, content: list):
        self.page_number = number
        self.content = content

    @property
    def items(self):
        return [data for data in self.content]

    def __iter__(self):
        return iter(self.content)


class Base:
    page_size = 10
    max_page_size = None

    def __init__(
        self,
        get_req_dict: Union[IndexedFieldStorage, None] = None,
    ):
        self._parser = Parser(
            path=os.path.join(os.path.dirname(__file__), "templates"),
            templates=("simple_pagination.html",),
        )
        self.total_pages = 0
        self._page_number = 1
        self.get_data = get_req_dict
        self._pages = []

    @property
    def pages(self):
        return self._pages

    @pages.setter
    def pages(self, value):
        self._pages = value
        self.total_pages = len(self._pages)

    @property
    def current_page(self):
        if not self.pages:
            raise NoPageError(f"No page for page number {self.page_number}")
        return self.pages[self.page_number - 1]

    @property
    def page_number(self):
        return self._page_number

    @page_number.setter
    def page_number(self, value):
        if isinstance(value, int):
            if value > self.total_pages or (
                self.max_page_size and value > self.max_page_size
            ):
                raise PageNumberOutOfRange("Page number is out of range")
            self._page_number = value
        elif isinstance(value, str) and value.isnumeric():
            self.page_number = int(value)
        else:
            raise InvalidPageNumber("Page number is of an invalid type")

    @property
    def next_page(self):
        if self.page_number < self.total_pages:
            return self.page_number + 1
        else:
            return self.page_number

    @property
    def previous_page(self):
        if self.page_number > 1:
            return self.page_number - 1
        else:
            return self.page_number

    @property
    def render_nav(self):
        ranges = self._determine_page_numbers()
        return self._parser.Parse(
            "simple_pagination.html",
            __paginator=self,
            __ranges=ranges,
            __query_url=self._query_url(),
        )

    def _query_url(self):
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
        return []

    def _determine_page_numbers(self):
        nav_end = min(self.previous_page + 4, self.total_pages + 1)
        if self.total_pages - self.page_number < 2:
            return range(max(0, self.previous_page - 2), nav_end)
        return range(self.previous_page, nav_end)

    def __iter__(self):
        return iter(self.pages)


class BasePagination(Base):
    def __init__(
        self,
        data: Iterable,
        get_req_dict: Union[IndexedFieldStorage, None] = None,
    ):
        super().__init__(get_req_dict)
        self.pages = list(_chunkify(data, self.page_size))

        if self.get_data and self.get_data.getfirst("page"):
            self.page_number = self.get_data.getfirst("page")


class SortableBase(BasePagination):
    def __init__(
        self,
        data: Iterable,
        columns: tuple,
        get_req_dict: IndexedFieldStorage,
    ):
        self.order = get_req_dict.getfirst("order", "ASC")
        self.sort = get_req_dict.getfirst("sort")
        self.columns = columns
        data = self.sort_data(data)
        super().__init__(data=data, get_req_dict=get_req_dict)

    def sort_data(self, data: Iterable) -> Union[Iterable, list]:
        return NotImplemented


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

    @property
    def render_nav(self):
        return self._parser.Parse(
            "simple_pagination.html",
            __paginator=self,
            __ranges=self._determine_page_numbers(),
            __query_url=self._query_url(),
        )

    @property
    def render_sortable_head(self):
        return self._parser.Parse(
            "sortable_table_head.html",
            __paginator=self,
        )

    @property
    def render_table(self):
        return self._parser.Parse(
            "simple_table.html",
            __paginator=self,
            __ranges=self._determine_page_numbers(),
            __query_url=self._query_url(),
        )


class OffsetPagination(Base):
    def __init__(
        self,
        method: Callable,
        get_req_dict: Union[IndexedFieldStorage, None] = None,
        **modelargs,
    ):
        super().__init__(get_req_dict)
        if self.get_data and self.get_data.getfirst("page"):
            # We cannot set self.page_number here because we need
            # to determine the total amount of pages first.
            self.requested_page = int(self.get_data.getfirst("page"))
        self.modelargs = modelargs
        self.method = method
        self._setup()

    def _setup(self):
        offset = self.page_size * (self.requested_page - 1)
        self.pages = self.method(
            offset=offset,
            limit=self.page_size,
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
        self._pages = [Page(self.requested_page, value)]
        self.total_pages = int(math.ceil(float(itemcount) / self.page_size))
