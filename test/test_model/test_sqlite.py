import os
import unittest
from pathlib import Path
from test.test_model.helpers import SqliteConnection
from test.test_model.records import BasicTestRecordSqlite
from test.test_model.test_model import BaseRecordTests, RecordTests

# Importing uWeb3 makes the SQLTalk library available as a side-effect


class SqliteTest(BaseRecordTests):
    """Tests for Record classes with a compound key."""

    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.record_class = BasicTestRecordSqlite
        # self.record_class._PRIMARY_KEY = 'ID'
        self.connection = SqliteConnection()
        with self.connection as cursor:
            cursor.Execute('DROP TABLE IF EXISTS "author"')
            cursor.Execute('DROP TABLE IF EXISTS "book"')
            cursor.Execute(
                """
                        CREATE TABLE "author" (
                        "ID"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "name"	TEXT NOT NULL
                        );
                    """
            )
            cursor.Execute(
                """CREATE TABLE "book" (
                        "ID"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "author" INTEGER,
                        "title" TEXT
                      )"""
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute('DROP TABLE IF EXISTS "author"')
            cursor.Execute('DROP TABLE IF EXISTS "book"')


class SqliteTransactionTest(RecordTests):
    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.record_class = BasicTestRecordSqlite
        self.connection = SqliteConnection()
        with self.connection as cursor:
            cursor.Execute('DROP TABLE IF EXISTS "author"')
            cursor.Execute('DROP TABLE IF EXISTS "book"')
            cursor.Execute(
                """
                        CREATE TABLE "author" (
                        "ID"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "name"	TEXT NOT NULL
                        );
                    """
            )
            cursor.Execute(
                """CREATE TABLE "book" (
                        "ID"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "author" INTEGER,
                        "title" TEXT
                      )"""
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute('DROP TABLE IF EXISTS "author"')
            cursor.Execute('DROP TABLE IF EXISTS "book"')

    def getsecondConnection(self):
        return SqliteConnection()


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
