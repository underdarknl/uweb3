import unittest
from test import test_model
from uweb3 import model


class PostgresTest(test_model.BaseRecordTests):
    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.connection = test_model.PostgresConnection()
        self.record_class = test_model.BasicTestRecord


class PostgresTransactionTest(unittest.TestCase):
    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.record_class = test_model.BasicTestRecord
        self.connection = test_model.PostgresConnection()
        with self.connection as cursor:
            cursor.Execute('DROP TABLE IF EXISTS "author"')
            cursor.Execute('DROP TABLE IF EXISTS "book"')
            cursor.Execute(
                """
                        CREATE TABLE "author" (
                        "ID"	SERIAL PRIMARY KEY,
                        "name"	TEXT NOT NULL
                        );
                    """
            )
            cursor.Execute(
                """CREATE TABLE "book" (
                        "ID"	SERIAL PRIMARY KEY,
                        "author" INTEGER,
                        "title" TEXT
                      )"""
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute('DROP TABLE IF EXISTS "author"')
            cursor.Execute('DROP TABLE IF EXISTS "book"')

    def getsecondConnection(self):
        return test_model.PostgresConnection()

    def testLoadPrimary(self):
        """[Record] Records can be loaded by primary key using FromPrimary()"""
        with self.connection as cursor:
            inserted = cursor.Insert(table="author", values={"name": "A. Chrstie"})
        author = test_model.Author.FromPrimary(self.connection, inserted.insertid)
        self.assertEqual(type(author), test_model.Author)
        self.assertEqual(len(author), 2)
        self.assertEqual(author.key, inserted.insertid)
        self.assertEqual(author["name"], "A. Chrstie")

    def testLoadPrimaryWithChangedKey(self):
        """[Record] Records can be loaded from alternative primary key"""
        with self.connection as cursor:
            inserted = cursor.Insert(table="author", values={"name": "B. Cartland"})

        # Adjust primary key field name
        test_model.Author._PRIMARY_KEY = "name"
        # Actual tests
        author = test_model.Author.FromPrimary(self.connection, "B. Cartland")
        self.assertEqual(type(author), test_model.Author)
        self.assertEqual(len(author), 2)
        self.assertEqual(author.key, author["name"])
        self.assertEqual(author["ID"], inserted.insertid)
        # Restore global state
        test_model.Author._PRIMARY_KEY = "ID"


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
