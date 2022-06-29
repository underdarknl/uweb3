import os
from operator import attrgetter, itemgetter
from typing import Iterable, Union
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


def _chunkify(iterable: Iterable, size: int) -> Iterable:
    """Yield successive chunks from iterable of length size."""
    items = list(iterable)
    for i in range(0, len(items), size):
        yield Page(i, items[i : i + size])


class Page:
    def __init__(self, number: int, content: list):
        self.page_number = number
        self.content = content

    @property
    def items(self):
        return [data for data in self.content]

    def __iter__(self):
        return iter(self.content)


class BasePagination:
    page_size = 10
    max_page_size = None

    def __init__(
        self, data: Iterable, get_req_dict: Union[IndexedFieldStorage, None] = None
    ):
        self.__parser = Parser(
            path=os.path.join(os.path.dirname(__file__), "templates"),
            templates=("simple_pagination.html",),
        )
        self._page_number = 1
        self.get_data = get_req_dict

        self.pages = list(_chunkify(data, self.page_size))
        self.total_pages = len(self.pages)

        if self.get_data and self.get_data.getfirst("page"):
            self.page_number = self.get_data.getfirst("page")

    def get_page(self, page_number: int):
        if not self.pages:
            raise NoPageError(f"No page for page number {page_number}")
        return self.pages[page_number]

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
        elif isinstance(value, str) and value in ("first", "last", "next", "prev"):
            self._page_number = self._determine_page(value)
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
        query_url = "".join(
            [f"&{key}={self.get_data.getfirst(key)}" for key in self.relevant_keys()]
        )
        return self.__parser.Parse(
            "simple_pagination.html",
            __paginator=self,
            __ranges=ranges,
            __query_url=query_url,
        )

    def relevant_keys(self):
        return []

    def _determine_page_numbers(self):
        nav_start = self.previous_page
        nav_end = min(nav_start + 4, self.total_pages + 1)
        if self.total_pages - self.page_number < 2:
            return range(nav_start - 2, nav_end)
        return range(nav_start, nav_end)

    def _determine_page(self, value: str):
        if value == "first":
            return 1
        if value == "last":
            return self.total_pages
        raise InvalidPageNumber(f"Value {value} for page number is not supported")

    def __iter__(self):
        return iter(self.pages)


class SortablePagination(BasePagination):
    def __init__(
        self, data: Iterable, get_req_dict: Union[IndexedFieldStorage, None] = None
    ):
        data = list(data)
        order = get_req_dict.getfirst("order", "ASC")
        if get_req_dict.getfirst(
            "sort",
        ):
            if order == "ASC":
                data.sort(
                    key=itemgetter(
                        get_req_dict.getfirst(
                            "sort",
                        )
                    ),
                    reverse=False,
                )
            else:
                data.sort(key=itemgetter(get_req_dict.getfirst("sort")), reverse=True)

        super().__init__(data=data, get_req_dict=get_req_dict)

    def relevant_keys(self):
        keys = super().relevant_keys()
        return keys + ["sort", "order"]
