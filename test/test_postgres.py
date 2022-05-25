import unittest
from test import test_model


class PostgresTest(test_model.BaseRecordTests):
    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.connection = test_model.PostgresConnection()
        self.record_class = test_model.BasicTestRecord


class PostgresTransactionTest(test_model.RecordTests):
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


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
