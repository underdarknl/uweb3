import unittest
from test.test_model.helpers import DatabaseConnection
from test.test_model.records import Book, Writer

from uweb3 import model


class NonStandardTableAndRelations(unittest.TestCase):
    """Verified autoloading works for records with an alternate table name."""

    def setUp(self):
        """Sets up the tests for the Record class."""
        self.connection = DatabaseConnection()
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `writers`")
            cursor.Execute("DROP TABLE IF EXISTS `book`")
            cursor.Execute(
                """CREATE TABLE `writers` (
                            `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
                            `name` varchar(32) NOT NULL,
                            PRIMARY KEY (`ID`)
                          ) ENGINE=InnoDB  DEFAULT CHARSET=utf8"""
            )
            cursor.Execute(
                """CREATE TABLE `book` (
                            `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
                            `author` smallint(5) unsigned NOT NULL,
                            `title` varchar(32) NOT NULL,
                            PRIMARY KEY (`ID`)
                          ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `writers`")
            cursor.Execute("DROP TABLE IF EXISTS `book`")

    def testVerifyNoLoad(self):
        """No loading is performed on a field that matches a class but no table"""
        book = Book(self.connection, {"writer": 1, "title": "Trouble Shooter"})
        self.assertEquals(book["writer"], 1)

    def testVerifyFailedLoad(self):
        """Loading is attempted for the field name matching the Record's table"""
        book = Book(self.connection, {"writers": 1, "title": "Hondo"})
        self.assertRaises(model.NotExistError, book.__getitem__, "writers")

    def testSuccessfulLoadWithTableName(self):
        """Loading works from the adjusted table name"""
        author = Writer.Create(self.connection, {"name": "R. Ludlum"})
        book = Book(self.connection, {"writers": 1, "title": "Bourne Identity"})
        self.assertEquals(book["writers"], author)

    def testLoadWithForeignRelationMapping(self):
        """Loading from alternative fieldname->table relation works"""
        author = Writer.Create(self.connection, {"name": "R.L. Stine"})
        book = Book.Create(self.connection, {"author": 1, "title": "Fright Camp"})
        self.assertRaises(
            self.connection.ProgrammingError, book.__getitem__, "author"
        )  # No table `author`
        Book._FOREIGN_RELATIONS = {"author": Writer}
        self.assertEqual(book["author"], author)
        del Book._FOREIGN_RELATIONS  # Don't persist changes to global state


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
