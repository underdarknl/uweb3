import unittest
from typing import Dict, List, Iterable
from uweb3 import model
from uweb3.pagination import (
    BasePagination,
    InvalidPageNumber,
    PageNumberOutOfRange,
    SortablePagination,
    OffsetPagination,
)
from functools import wraps
from itertools import zip_longest
from test.test_model import DatabaseConnection


def dict_from_iterable(data: Iterable) -> List[Dict]:
    return [{"ID": k, "name": v} for k, v in enumerate(data)]


def parameterize(names: str, data):
    def decorator(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            parameters = [x.strip() for x in names.split(",")]

            for item in data:
                fun(*args, **dict(zip_longest(parameters, item)), **kwargs)

        return wrapper

    return decorator


class MockIndexedFieldStorage(dict):
    def getfirst(self, key, default=None):
        return self.get(key, default)


class TestBasePagination(unittest.TestCase):
    def setUp(self) -> None:
        self.data = dict_from_iterable("abcdefghijklmnopqrstuvwxyz")
        self.paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": 1}),  # type: ignore
            page_size=5,
        )

    def test_page_count(self):
        """Test to ensure that the correct ammount of pages are generated"""
        paginator = BasePagination(self.data, page_size=1)  # type: ignore
        assert 26 == paginator.total_pages

        paginator = BasePagination("12345", page_size=1)  # type: ignore
        assert 5 == paginator.total_pages

    def test_current_page_number(self):
        """Validate that the correct page number is loaded"""
        paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": 1}),  # type: ignore
            page_size=1,
        )
        assert 1 == paginator.page_number

        paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": 10}),  # type: ignore
            page_size=1,
        )
        assert 10 == paginator.page_number

        paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": "10"}),  # type: ignore
            page_size=1,
        )
        assert 10 == paginator.page_number

        paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": "-1"}),  # type: ignore
            page_size=1,
        )
        assert 1 == paginator.page_number

    def test_page_content(self):
        """Validate that no values are skipped when going to the next page.

        This test is typed out explicitly to improve readability.
        """
        assert 5 == len(self.paginator.current_page)

        self.assertListEqual(
            self.paginator.current_page.items,
            [
                {"ID": 0, "name": "a"},
                {"ID": 1, "name": "b"},
                {"ID": 2, "name": "c"},
                {"ID": 3, "name": "d"},
                {"ID": 4, "name": "e"},
            ],
        )
        self.assertListEqual(
            self.paginator.pages[1].items,
            [
                {"ID": 5, "name": "f"},
                {"ID": 6, "name": "g"},
                {"ID": 7, "name": "h"},
                {"ID": 8, "name": "i"},
                {"ID": 9, "name": "j"},
            ],
        )
        self.assertListEqual(
            self.paginator.pages[2].items,
            [
                {"ID": 10, "name": "k"},
                {"ID": 11, "name": "l"},
                {"ID": 12, "name": "m"},
                {"ID": 13, "name": "n"},
                {"ID": 14, "name": "o"},
            ],
        )
        self.assertListEqual(
            self.paginator.pages[3].items,
            [
                {"ID": 15, "name": "p"},
                {"ID": 16, "name": "q"},
                {"ID": 17, "name": "r"},
                {"ID": 18, "name": "s"},
                {"ID": 19, "name": "t"},
            ],
        )
        self.assertListEqual(
            self.paginator.pages[4].items,
            [
                {"ID": 20, "name": "u"},
                {"ID": 21, "name": "v"},
                {"ID": 22, "name": "w"},
                {"ID": 23, "name": "x"},
                {"ID": 24, "name": "y"},
            ],
        )
        self.assertListEqual(
            self.paginator.pages[5].items,
            [
                {"ID": 25, "name": "z"},
            ],
        )

    def test_page_out_of_range(self):
        """Validate that PageNumberOutOfRange exception is riased when
        attempting to access a page that is out of range."""
        with self.assertRaises(PageNumberOutOfRange):
            BasePagination(
                self.data,
                get_req_dict=MockIndexedFieldStorage({"page": 500}),  # type: ignore
                page_size=1,
            )

    def test_invalid_page_number(self):
        """Validate that when attempting to access an invalid page
        the user will be redirected to page number 1."""
        paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": "notanumber"}),  # type: ignore
            page_size=1,
        )

        assert 1 == paginator.page_number

    @parameterize(
        "input, page, expected",
        [
            ([], 1, range(1, 1)),
            ([1], 1, range(1, 2)),
            ([1, 2], 1, range(1, 3)),
            ([1, 2, 3], 1, range(1, 4)),
            ([1, 2, 3], 2, range(1, 4)),
            ([1, 2, 3], 3, range(1, 4)),
        ],
    )
    def test_shown_page_numbers(self, input, page, expected):
        paginator = BasePagination(
            input,
            get_req_dict=MockIndexedFieldStorage({"page": page}),  # type: ignore
            page_size=1,
        )
        assert expected == paginator._determine_page_numbers()


class TestSortablePagination(unittest.TestCase):
    def setUp(self) -> None:
        self.data = dict_from_iterable("abcdefghijklmnopqrstuvwxyz")

    def test_query_url_desc(self):
        """Validate that the current page is sorted DESC"""
        paginator = SortablePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "ID", "order": "DESC"}),  # type: ignore
            columns=("ID", "name"),
            page_size=5,
        )

        self.assertListEqual(
            paginator.current_page.items,
            [
                {"ID": 25, "name": "z"},
                {"ID": 24, "name": "y"},
                {"ID": 23, "name": "x"},
                {"ID": 22, "name": "w"},
                {"ID": 21, "name": "v"},
            ],
        )

    def test_query_url_asc(self):
        """Validate that the current page is sorted DESC"""
        paginator = SortablePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "ID", "order": "ASC"}),  # type: ignore
            columns=("ID", "name"),
            page_size=5,
        )

        self.assertListEqual(
            paginator.current_page.items,
            [
                {"ID": 0, "name": "a"},
                {"ID": 1, "name": "b"},
                {"ID": 2, "name": "c"},
                {"ID": 3, "name": "d"},
                {"ID": 4, "name": "e"},
            ],
        )

    def test_no_specify(self):
        """Validate that list is not sorted or ordered when keys are missing"""
        paginator = SortablePagination(
            dict_from_iterable("bacde"),
            get_req_dict=MockIndexedFieldStorage({"page": 1}),  # type: ignore
            columns=("ID", "name"),
            page_size=5,
        )

        self.assertListEqual(
            paginator.current_page.items,
            [
                {"ID": 0, "name": "b"},
                {"ID": 1, "name": "a"},
                {"ID": 2, "name": "c"},
                {"ID": 3, "name": "d"},
                {"ID": 4, "name": "e"},
            ],
        )

    def test_order_column(self):
        """Validate that ordering by key other than ID also works."""
        paginator = SortablePagination(
            dict_from_iterable(["aaa", "bbb", "ccc", "ddd"]),
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "name", "order": "DESC"}),  # type: ignore
            columns=("ID", "name"),
            page_size=5,
        )
        self.assertListEqual(
            paginator.current_page.items,
            [
                {"ID": 3, "name": "ddd"},
                {"ID": 2, "name": "ccc"},
                {"ID": 1, "name": "bbb"},
                {"ID": 0, "name": "aaa"},
            ],
        )


class Items(model.Record):
    pass


class RecordTests(unittest.TestCase):
    """Online tests of methods and behavior of the Record class."""

    def setUp(self):
        """Sets up the tests for the Record class."""
        self.connection = DatabaseConnection()
        self.record_class = Items
        self.data = tuple(f"item{i}" for i in range(0, 25))
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `items`")
            cursor.Execute(
                """CREATE TABLE `items` (
                            `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
                            `name` varchar(32) NOT NULL,
                            PRIMARY KEY (`ID`)
                        ) ENGINE=InnoDB  DEFAULT CHARSET=utf8"""
            )

            cursor.executemany(
                """
                            INSERT INTO items(name) VALUES(%s)""",
                self.data,
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `items`")

    def test_page_content(self):
        """Validate that the current page is loaded correctly from the model method."""
        paginator = OffsetPagination(
            self.record_class.List,
            modelargs=dict(connection=self.connection),
            page_size=3,
        )
        assert 3 == len(paginator.current_page.items)
        assert 9 == paginator.total_pages
        self.assertListEqual(
            paginator.current_page.items,
            [
                Items(None, {"ID": 1, "name": "item0"}),
                Items(None, {"ID": 2, "name": "item1"}),
                Items(None, {"ID": 3, "name": "item2"}),
            ],
        )

    def test_page_content_limit(self):
        """Validate that the current page is loaded correctly from the model method."""
        limit = 2
        paginator = OffsetPagination(
            self.record_class.List,
            modelargs=dict(connection=self.connection, limit=limit),
            page_size=3,
        )
        assert limit == len(paginator.current_page.items)
        assert 9 == paginator.total_pages
        self.assertListEqual(
            paginator.current_page.items,
            [
                Items(None, {"ID": 1, "name": "item0"}),
                Items(None, {"ID": 2, "name": "item1"}),
            ],
        )

    def test_load_current_page_only(self):
        """Validate that only the current page is loaded but the paginator
        still calculates the amount of total pages."""
        paginator = OffsetPagination(
            self.record_class.List,
            modelargs=dict(connection=self.connection),
            page_size=3,
        )
        assert 3 == len(paginator.current_page.items)
        assert 9 == paginator.total_pages
        assert 1 == len(paginator.pages)


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
