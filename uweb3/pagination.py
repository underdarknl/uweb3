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
        self._page_number = 0
        self.get_data = get_req_dict

        self.pages = list(_chunkify(data, self.page_size))
        self.total_pages = len(self.pages) - 1

        if self.get_data.getfirst("page"):
            self.page_number = self.get_data.getfirst("page")

    def get_page(self, page_number: int):
        if not self.pages:
            raise NoPageError(f"No page for page number {page_number}")
        return self.pages[page_number]

    @property
    def current_page(self):
        if not self.pages:
            raise NoPageError(f"No page for page number {self.page_number}")
        return self.pages[self.page_number]

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
        if self.page_number < self.total_pages - 1:
            return self.page_number + 1
        else:
            return self.page_number

    @property
    def previous_page(self):
        if self.page_number > 0:
            return self.page_number - 1
        else:
            return self.page_number

    @property
    def render_nav(self):
        nav_start = self.previous_page
        nav_end = min(nav_start + 4, self.total_pages + 1)
        ranges = range(nav_start, nav_end)
        return Parser().ParseString(
            """
            <nav class="pagination">
                <ol>
                    {{ if [__paginator:page_number] != 0 }}
                        <li><a href="?page=first">First</a></li>
                    {{ endif }}
                    {{ for p in [__ranges] }}
                        <li><a href="?page=[p]">[p]</a></li>
                    {{ endfor }}
                    <li><a href="?page=[__paginator:previous_page]">Previous</a></li>
                    {{ if [__paginator:page_number] <  [__paginator:total_pages]  }}
                        <li><a href="?page=[__paginator:next_page]">Next</a></li>
                    {{ endif }}
                    {{ if [__paginator:page_number] != [__paginator:total_pages] }}
                        <li><a href="?page=last">Last</a></li>
                    {{ endif }}
                </ol>
            </nav>
            """,
            __paginator=self,
            __ranges=ranges,
        )

    def _determine_page(self, value: str):
        if value == "first":
            return 0
        if value == "last":
            return self.total_pages
        raise InvalidPageNumber(f"Value {value} for page number is not supported")

    def __iter__(self):
        return iter(self.pages)
