import unittest
from typing import Dict, List, Iterable
from uweb3 import model
from uweb3.libs.safestring import HTMLsafestring
from uweb3.pagination import (
    BasePagination,
    InvalidPageNumber,
    PageNumberOutOfRange,
    SortablePagination,
    OffsetPagination,
)
from uweb3.templateparser import Parser
from functools import wraps
from itertools import zip_longest
from test.test_model import DatabaseConnection

import string


class Items(model.Record):
    """Record class for OffsetPagination tests"""


def dict_from_iterable(data: Iterable) -> List[Dict]:
    return [{"ID": k, "name": v} for k, v in enumerate(data)]


def parameterize(params: str, values):
    """Decorator that can be used like pytest.mark.parameterize."""

    def decorator(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            parameters = [x.strip() for x in params.split(",")]

            for item in values:
                fun(*args, **dict(zip_longest(parameters, item)), **kwargs)

        return wrapper

    return decorator


def htmlsafe_no_whitespace(target):
    """Remove \n from string for string comparison purposes"""
    return target.translate({ord(c): None for c in string.whitespace})


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

    @parameterize(
        "input, page_size, expected",
        [
            ("1", 1, 1),
            ("12", 1, 2),
            ("12345", 1, 5),
            ("12345", 2, 3),
            ("123456", 3, 2),
            ("123456", 10, 1),
        ],
    )
    def test_page_counts(self, input, page_size, expected):
        paginator = BasePagination(input, page_size=page_size)  # type: ignore
        assert expected == paginator.total_pages

    @parameterize(
        "page_number, expected_page_number",
        [
            (1, 1),
            (10, 10),
            ("10", 10),
            ("-1", 1),
            ("0", 1),
            (0, 1),
            ("-100", 1),
        ],
    )
    def test_current_page_number(self, page_number, expected_page_number):
        """Validate that the correct page number is loaded"""
        paginator = BasePagination(
            self.data,
            get_req_dict=MockIndexedFieldStorage({"page": page_number}),  # type: ignore
            page_size=1,
        )
        assert expected_page_number == paginator.page_number

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

    def test_render_nav(self):
        paginator = BasePagination(
            "12345",
            get_req_dict=MockIndexedFieldStorage({"page": 1}),  # type: ignore
            page_size=5,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
                <nav class="pagination">
                    <ol>
                        <li>
                            <a href="?page=1">1</a>
                        </li>
                    </ol>
                </nav>
                """
        )

        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_multi_pages_nav(self):
        """Validate that the correct menu rendered."""
        paginator = BasePagination(
            "12345",
            get_req_dict=MockIndexedFieldStorage({"page": 1}),  # type: ignore
            page_size=1,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
            <nav class="pagination">
                <ol>
                    <li><a href="?page=1">1</a></li>
                    <li><a href="?page=2">2</a></li>
                    <li><a href="?page=3">3</a></li>
                    <li><a href="?page=4">4</a></li>
                    <li><a href="?page=2">Next</a></li>
                    <li><a href="?page=5">Last</a></li>
                </ol>
            </nav>"""
        )

        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_from_page_nav(self):
        """Validate that rendering from a specific page renders the
        correct navigation menu."""
        paginator = BasePagination(
            "12345",
            get_req_dict=MockIndexedFieldStorage({"page": 3}),  # type: ignore
            page_size=1,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
            <nav class="pagination">
                <ol>
                    <li><a href="?page=1">First</a></li>
                    <li><a href="?page=2">2</a></li>
                    <li><a href="?page=3">3</a></li>
                    <li><a href="?page=4">4</a></li>
                    <li><a href="?page=5">5</a></li>
                    <li><a href="?page=2">Previous</a></li>
                    <li><a href="?page=4">Next</a></li>
                    <li><a href="?page=5">Last</a></li>
                </ol>
            </nav>"""
        )

        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_last_page_nav(self):
        """Validate that rendering from a specific page renders the
        correct navigation menu."""
        paginator = BasePagination(
            "12345",
            get_req_dict=MockIndexedFieldStorage({"page": 5}),  # type: ignore
            page_size=1,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
            <nav class="pagination">
                <ol>
                    <li><a href="?page=1">First</a></li>
                    <li><a href="?page=2">2</a></li>
                    <li><a href="?page=3">3</a></li>
                    <li><a href="?page=4">4</a></li>
                    <li><a href="?page=5">5</a></li>
                    <li><a href="?page=4">Previous</a></li>
                </ol>
            </nav>"""
        )

        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )


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

    def test_render_nav_no_query(self):
        """Validate that the navigation for the paginator is rendered
        with no query parameters"""
        paginator = SortablePagination(
            [
                {"ID": 1, "name": "test"},
            ],
            columns=("ID", "name"),
            get_req_dict=MockIndexedFieldStorage({"page": 1}),  # type: ignore
            page_size=5,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
                <nav class="pagination">
                    <ol>
                        <li>
                            <a href="?page=1">1</a>
                        </li>
                    </ol>
                </nav>
                """
        )
        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_nav_query(self):
        """Validate that the navigation for the paginator is rendered
        with the correct query parameters."""
        paginator = SortablePagination(
            [
                {"ID": 1, "name": "test"},
            ],
            columns=("ID", "name"),
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "ID", "order": "ASC"}),  # type: ignore
            page_size=5,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
                <nav class="pagination">
                    <ol>
                        <li>
                            <a href="?page=1&amp;sort=ID&amp;order=ASC">1</a>
                        </li>
                    </ol>
                </nav>
                """
        )
        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_nav_other_key_query(self):
        """Validate that the navigation for the paginator renders
        different columns corretly too."""
        paginator = SortablePagination(
            [
                {"ID": 1, "name": "test"},
            ],
            columns=("ID", "name"),
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "name", "order": "DESC"}),  # type: ignore
            page_size=5,
        )

        parsed = Parser().ParseString("[paginator:render_nav]", paginator=paginator)
        expected = HTMLsafestring(
            """
                <nav class="pagination">
                    <ol>
                        <li>
                            <a href="?page=1&amp;sort=name&amp;order=DESC">1</a>
                        </li>
                    </ol>
                </nav>
                """
        )
        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_sortable_head_desc(self):
        """Validate that order key is ASC when the table is currently sorted
        DESC on key name.

        ID should default to ASC when its not being targeted.
        """
        paginator = SortablePagination(
            [
                {"ID": 1, "name": "test"},
            ],
            columns=("ID", "name"),
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "name", "order": "DESC"}),  # type: ignore
            page_size=5,
        )

        parsed = Parser().ParseString(
            "[paginator:render_sortable_head]", paginator=paginator
        )
        expected = HTMLsafestring(
            """
            <thead>
                <tr>
                    <th class="sortable">ID
                        <a href="?page=1&sort=ID&order=ASC"></a>
                    </th>
                    <th class="ascending">name
                        <a href="?page=1&sort=name&order=ASC"></a>
                    </th>
                </tr>
            </thead>"""
        )
        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_sortable_head_asc(self):
        """Validate that order key is DESC when the table is currently sorted
        ASC on key name.

        Furthermore the ID should still be pointing towards the
        default sort of ASC.
        """
        paginator = SortablePagination(
            [
                {"ID": 1, "name": "test"},
            ],
            columns=("ID", "name"),
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "name", "order": "ASC"}),  # type: ignore
            page_size=5,
        )

        parsed = Parser().ParseString(
            "[paginator:render_sortable_head]", paginator=paginator
        )
        expected = HTMLsafestring(
            """
            <thead>
                <tr>
                    <th class="sortable">ID
                        <a href="?page=1&sort=ID&order=ASC"></a>
                    </th>
                    <th class="descending">name
                        <a href="?page=1&sort=name&order=DESC"></a>
                    </th>
                </tr>
            </thead>"""
        )
        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )

    def test_render_table(self):
        """Test rendering a table as a whole."""
        paginator = SortablePagination(
            [
                {"ID": 1, "name": "test"},
            ],
            columns=("ID", "name"),
            get_req_dict=MockIndexedFieldStorage({"page": 1, "sort": "name", "order": "ASC"}),  # type: ignore
            page_size=5,
        )
        parsed = Parser().ParseString("[paginator:render_table]", paginator=paginator)
        expected = """
                <table>
                    <thead>
                        <tr>
                            <th class="sortable">ID <a href="?page=1&sort=ID&order=ASC"></a> </th>
                            <th class="descending">name <a href="?page=1&sort=name&order=DESC"></a> </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>1</td>
                            <td>test</td>
                        </tr>
                    </tbody>
                </table>
                <nav class="pagination">
                    <ol>
                        <li><a href="?page=1&amp;sort=name&amp;order=ASC">1</a></li>
                    </ol>
                </nav>"""

        self.assertAlmostEqual(
            htmlsafe_no_whitespace(parsed), htmlsafe_no_whitespace(expected)
        )


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
