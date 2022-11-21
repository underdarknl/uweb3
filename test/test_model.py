#!/usr/bin/python3
"""Test suite for the database abstraction module (model)."""

# Too many public methods
# pylint: disable=R0904

import hashlib
import json
import os

# Standard modules
import unittest
from pathlib import Path

# Unittest target
from uweb3 import model, request
from uweb3.model import CookieEncoder, SecureCookie, SupportedHashes

# Importing uWeb3 makes the SQLTalk library available as a side-effect
from uweb3.libs.sqltalk import mysql, safe_cookie, sqlite


# ##############################################################################
# Record classes for testing
#
class BasicTestRecord(model.Record):
    """Test record for offline tests."""


class BasicTestRecordSqlite(model.Record):
    """Test record for offline tests."""

    _CONNECTOR = "sqlite"


class Author(model.Record):
    """Author class for testing purposes."""


class Book(model.Record):
    """Book class for testing purposes."""


class Session(model.SecureCookie):
    """Session class for cookie testing purposes."""


class Writer(model.Record):
    """Writer class for testing purposes, will manage `writers` table."""

    _TABLE = "writers"


class VersionedAuthor(model.VersionedRecord):
    """Versioned author table for testing purposes."""


class VersionedBook(model.VersionedRecord):
    """Versioned Book class for testing purposes."""


class Compounded(model.Record):
    """Compound key record for generic storage."""

    _PRIMARY_KEY = "first", "second"


# ##############################################################################
# Start of tests
#
class BaseRecordTests(unittest.TestCase):
    """Offline tests of methods and behavior of the BaseRecord class."""

    def setUp(self):
        """Sets up the tests for the offline Record test."""
        self.record_class = BasicTestRecord

    def testTableName(self):
        """[BaseRecord] TableName returns the expected value and obeys _TABLE"""
        tablename = (
            self.record_class.__name__[0].lower() + self.record_class.__name__[1:]
        )
        self.assertEqual(self.record_class.TableName(), tablename)
        self.record_class._TABLE = "WonderfulSpam"
        self.assertEqual(self.record_class.TableName(), "WonderfulSpam")

    def testPrimaryKey(self):
        """[BaseRecord] Primary key value on `key` property, default field 'ID'"""
        record = self.record_class(None, {"ID": 12, "name": "J.R.R. Tolkien"})
        self.assertEqual(record.key, 12)

    def testPrimaryKeyChanges(self):
        """[BaseRecord] Defining _PRIMARY_KEY overrides default value"""
        record = self.record_class(None, {"ID": 12, "name": "K. May"})
        self.record_class._PRIMARY_KEY = "name"
        self.assertEqual(record.key, "K. May")

    def testEquality(self):
        """[BaseRecord] Records of the same content are equal to eachother"""
        record_one = self.record_class(None, {"ID": 2, "name": "Rowling"})
        record_two = self.record_class(None, {"ID": 2, "name": "Rowling"})
        record_three = self.record_class(None, {"ID": 3, "name": "Rowling"})
        record_four = self.record_class(None, {"ID": 2, "name": "Rowling", "x": 2})
        self.assertFalse(record_one is record_two)
        self.assertEqual(record_one, record_two)
        self.assertNotEqual(record_one, record_three)
        self.assertNotEqual(record_one, record_four)


class RecordTests(unittest.TestCase):
    """Online tests of methods and behavior of the Record class."""

    def setUp(self):
        """Sets up the tests for the Record class."""
        self.connection = DatabaseConnection()
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `author`")
            cursor.Execute("DROP TABLE IF EXISTS `book`")
            cursor.Execute(
                """CREATE TABLE `author` (
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
            cursor.Execute("DROP TABLE IF EXISTS `author`")
            cursor.Execute("DROP TABLE IF EXISTS `book`")

    def getsecondConnection(self):
        return DatabaseConnection()

    def testLoadPrimary(self):
        """[Record] Records can be loaded by primary key using FromPrimary()"""
        with self.connection as cursor:
            inserted = cursor.Insert(table="author", values={"name": "A. Chrstie"})
        author = Author.FromPrimary(self.connection, inserted.insertid)
        self.assertEqual(type(author), Author)
        self.assertEqual(len(author), 2)
        self.assertEqual(author.key, inserted.insertid)
        self.assertEqual(author["name"], "A. Chrstie")

    def testLoadPrimaryWithChangedKey(self):
        """[Record] Records can be loaded from alternative primary key"""
        with self.connection as cursor:
            inserted = cursor.Insert(table="author", values={"name": "B. Cartland"})
        # Adjust primary key field name
        Author._PRIMARY_KEY = "name"
        # Actual tests
        author = Author.FromPrimary(self.connection, "B. Cartland")
        self.assertEqual(type(author), Author)
        self.assertEqual(len(author), 2)
        self.assertEqual(author.key, author["name"])
        self.assertEqual(author["ID"], inserted.insertid)
        # Restore global state
        Author._PRIMARY_KEY = "ID"

    def testCreateRecord(self):
        """Database records can be created using Create()"""
        new_author = Author.Create(self.connection, {"name": "W. Shakespeare"})
        author = Author.FromPrimary(self.connection, new_author.key)
        self.assertEqual(author["name"], "W. Shakespeare")

    def testCreateRecordWithBadField(self):
        """Database record creation fails if there are unknown fields present"""
        self.assertRaises(
            model.BadFieldError,
            Author.Create,
            self.connection,
            {"name": "L. Tolstoy", "email": "leo@tolstoy.ru"},
        )

    def testUpdateRecord(self):
        """The record can be given new values and these are properly stored"""
        author = Author.Create(self.connection, {"name": "B. King"})
        author["name"] = "S. King"
        author.Save()
        same_author = Author.FromPrimary(self.connection, 1)
        self.assertEqual(same_author["name"], "S. King")
        self.assertEqual(same_author, author)

    def testUpdateRecordWithBadField(self):
        """Database record updating fails if there are unknown fields present"""
        author = Author.Create(self.connection, {"name": "A. Pushkin"})
        author["specialty"] = "poetry"
        self.assertRaises(model.BadFieldError, author.Save)

    def testUpdatePrimaryKey(self):
        """Saving with an updated primary key properly saved the record"""
        author = Author.Create(self.connection, {"name": "C. Dickens"})
        self.assertEqual(author.key, 1)
        author["ID"] = 101
        author.Save()
        self.assertRaises(model.NotExistError, Author.FromPrimary, self.connection, 1)
        same_author = Author.FromPrimary(self.connection, 101)
        self.assertEqual(same_author, author)

    def testLoadRelated(self):
        """Fieldnames that match tablenames trigger automatic loading"""
        Author.Create(self.connection, {"name": "D. Koontz"})
        book = Book(self.connection, {"author": 1})
        self.assertEqual(type(book["author"]), Author)
        self.assertEqual(book["author"]["name"], "D. Koontz")
        self.assertEqual(book["author"].key, 1)

    def testLoadRelatedFailure(self):
        """Automatic loading raises NotExistError if the foreign record is absent"""
        book = Book(self.connection, {"author": 1})
        self.assertRaises(model.NotExistError, book.__getitem__, "author")

    def testLoadRelatedSuppressedForNone(self):
        """Automatic loading is not attempted when the field value is `None`"""
        book = Book(self.connection, {"author": None})
        self.assertEqual(book["author"], None)

    def testManualCommit(self):
        """Validates that manual committing is indeed working"""
        Author.autocommit(self.connection, False)
        new_author = Author.Create(self.connection, {"name": "W. Shakespeare"})
        Author.commit(self.connection)
        author = Author.FromPrimary(self.connection, new_author.key)
        self.assertEqual(author["name"], "W. Shakespeare")

    def testMultipleRecordsInManualCommit(self):
        """Validates that all queries in a transaction are propperly committed when doing so manually"""
        Author.autocommit(self.connection, False)
        for i in range(5):
            Author.Create(self.connection, {"name": "W. Shakespeare"})
        Author.commit(self.connection)
        authors = list(Author.List(self.connection))
        self.assertEqual(5, len(authors))

    def testMultipleRecordsRollback(self):
        """Validates that a rollback indeed removes all queries from the transaction"""
        Author.autocommit(self.connection, False)
        for i in range(5):
            Author.Create(self.connection, {"name": "W. Shakespeare"})
        Author.rollback(self.connection)
        authors = list(Author.List(self.connection))
        self.assertEqual(0, len(authors))

    def testDirtyRead(self):
        """Validates that a dirty read is not possible"""
        seperate_connection = self.getsecondConnection()
        Author.autocommit(self.connection, False)
        new_author = Author.Create(self.connection, {"name": "W. Shakespeare"})
        self.assertRaises(
            model.NotExistError, Author.FromPrimary, seperate_connection, new_author.key
        )

    def testUncommitedTransaction(self):
        """Validates that a commited transaction is visible for another connection"""
        seperate_connection = self.getsecondConnection()
        Author.autocommit(self.connection, False)
        new_author = Author.Create(self.connection, {"name": "W. Shakespeare"})
        Author.commit(self.connection)
        author = Author.FromPrimary(seperate_connection, new_author.key)
        self.assertEqual(author["name"], "W. Shakespeare")

    def testDelete(self):
        """Database records can be created using Create()"""
        new_author = Author.Create(self.connection, {"name": "W. Shakespeare"})
        author = Author.FromPrimary(self.connection, new_author.key)
        self.assertEqual(author["name"], "W. Shakespeare")
        author.Delete()
        self.assertRaises(
            model.NotExistError, Author.FromPrimary, self.connection, new_author.key
        )

    def testRollBack(self):
        """No record should be found after the transaction was rolled back"""
        Author.autocommit(self.connection, False)
        new_author = Author.Create(self.connection, {"name": "W. Shakespeare"})
        Author.rollback(self.connection)
        Author.autocommit(self.connection, True)
        self.assertRaises(
            model.NotExistError, Author.FromPrimary, self.connection, new_author.key
        )


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


class VersionedRecordTests(unittest.TestCase):
    """Tests for the VersionedRecord class."""

    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.connection = DatabaseConnection()
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `versionedAuthor`")
            cursor.Execute("DROP TABLE IF EXISTS `versionedBook`")
            cursor.Execute(
                """CREATE TABLE `versionedAuthor` (
                            `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
                            `versionedAuthorID` smallint(5) unsigned NOT NULL,
                            `name` varchar(32) NOT NULL,
                            PRIMARY KEY (`ID`),
                            KEY `recordKey` (`versionedAuthorID`)
                          ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
            )
            cursor.Execute(
                """CREATE TABLE `versionedBook` (
                            `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
                            `versionedBookID` smallint(5) unsigned NOT NULL,
                            `versionedAuthor` smallint(5) unsigned NOT NULL,
                            `title` varchar(32) NOT NULL,
                            PRIMARY KEY (`ID`),
                            KEY `recordKey` (`versionedBookID`)
                          ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS `versionedAuthor`")
            cursor.Execute("DROP TABLE IF EXISTS `versionedBook`")

    def testRecordKeyName(self):
        """[Versioned] Versioning key name follows table name unless specified"""
        # Accessing protected members to check intended behavior
        # pylint: disable=W0212
        # Sanity checks, we're changing global scope here
        self.assertTrue(VersionedAuthor._TABLE is None)
        self.assertTrue(VersionedAuthor._RECORD_KEY is None)
        # Actual tests
        self.assertEqual(VersionedAuthor.RecordKey(), "versionedAuthorID")
        VersionedAuthor._TABLE = "author"
        self.assertEqual(VersionedAuthor.RecordKey(), "authorID")
        VersionedAuthor._RECORD_KEY = "recordKey"
        self.assertEqual(VersionedAuthor.RecordKey(), "recordKey")
        # Restore global state
        VersionedAuthor._TABLE = None
        VersionedAuthor._RECORD_KEY = None

    def testCreateVersioned(self):
        """[Versioned] Creating and loading a record from identifier works"""
        author = VersionedAuthor.Create(self.connection, {"name": "J. Grisham"})
        loaded = VersionedAuthor.FromIdentifier(self.connection, author.identifier)
        self.assertEqual(loaded["name"], "J. Grisham")
        self.assertEqual(loaded, author)

    def testUpdateVersioned(self):
        """[Versioned] Updating records and loading from identifier works"""
        author = VersionedAuthor.Create(self.connection, {"name": "Z. Gray"})
        initial_primary = author.key
        author["name"] = "Z. Grey"
        author.Save()
        self.assertNotEqual(author.key, initial_primary)
        # Loading from identifier gives updated name
        loaded = VersionedAuthor.FromIdentifier(self.connection, author.identifier)
        self.assertEqual(loaded["name"], "Z. Grey")
        # Loading from old primary key gives old name
        loaded = VersionedAuthor.FromPrimary(self.connection, initial_primary)
        self.assertEqual(loaded["name"], "Z. Gray")

    def testListVersions(self):
        """[Versioned] Listing versions works, and happens in [old]-->[new] order"""
        author = VersionedAuthor.Create(self.connection, {"name": "A. Martin"})
        author["name"] = "A. Rice"
        author.Save()
        versions = list(VersionedAuthor.Versions(self.connection, author.identifier))
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["name"], "A. Martin")
        self.assertEqual(versions[1]["name"], "A. Rice")

    def testRelationsBasedOnIdentifier(self):
        """[Versioned] Related loading defaults to using FromIdentifier"""
        # Set up records with different record keys and identifiers
        collins = VersionedAuthor.Create(self.connection, {"name": "K. Collins"})
        collins["name"] = "J. Collins"
        collins.Save()
        patten = VersionedAuthor.Create(self.connection, {"name": "G. Patten"})
        # Verify sanity of keys and identifiers
        self.assertEqual(collins.key, 2)
        self.assertEqual(collins.identifier, 1)
        self.assertEqual(patten.key, 3)
        self.assertEqual(patten.identifier, 2)
        # Create book with foreign relation to author and perform actual test
        book = VersionedBook(
            self.connection, {"title": "The Diamond Sport", "versionedAuthor": 2}
        )
        self.assertEqual(book["versionedAuthor"], patten)

    def testRelationsWithModifiedLoadRelationsMethod(self):
        """[Versioned] Related loading can be controlled with _LOAD_METHOD"""
        # Accessing protected members to verify and modify behavior
        # pylint: disable=W0212
        # Sanity checks, we're changing global scope here
        self.assertEqual(VersionedBook._LOAD_METHOD, "FromIdentifier")
        # Actual tests
        VersionedAuthor._LOAD_METHOD = "FromPrimary"
        author = VersionedAuthor.Create(self.connection, {"name": "L. Amour"})
        author["name"] = "L. L'Amour"
        author.Save()
        book = VersionedBook(
            self.connection, {"title": "The Riders of High Rock", "versionedAuthor": 1}
        )
        self.assertEqual(book["versionedAuthor"]["name"], "L. Amour")
        latest_version = VersionedAuthor.FromIdentifier(self.connection, 1)
        self.assertEqual(latest_version["name"], "L. L'Amour")
        # Restore global state
        VersionedBook._LOAD_METHOD = "FromIdentifier"

    def testRelationsUsingCustomForeignRelations(self):
        """[Versioned] Related loading method can be set with _FOREIGN_RELATIONS"""
        # Accessing protected members to verify and modify behavior
        # pylint: disable=W0212
        # Sanity checks, we're changing global scope here
        self.assertEqual(VersionedBook._FOREIGN_RELATIONS, {})
        # Actual tests
        VersionedBook._FOREIGN_RELATIONS = {
            "versionedAuthor": {"class": "VersionedAuthor", "loader": "FromPrimary"}
        }
        author = VersionedAuthor.Create(self.connection, {"name": "H. Alger"})
        author["name"] = "H. Alger, Jr."
        author.Save()
        book = VersionedBook(
            self.connection, {"title": "Voices of the Past", "versionedAuthor": 1}
        )
        self.assertEqual(book["versionedAuthor"]["name"], "H. Alger")
        latest_version = VersionedAuthor.FromIdentifier(self.connection, 1)
        self.assertEqual(latest_version["name"], "H. Alger, Jr.")
        # Restore global state
        VersionedBook._FOREIGN_RELATIONS = {}


class CompoundKeyRecordTests(unittest.TestCase):
    """Tests for Record classes with a compound key."""

    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.connection = DatabaseConnection()
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS`compounded`")
            cursor.Execute(
                """CREATE TABLE `compounded` (
                            `first` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
                            `second` smallint(5) unsigned NOT NULL,
                            `message` varchar(32) NOT NULL,
                            PRIMARY KEY (`first`, `second`)
                          ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
            )

    def tearDown(self):
        with self.connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS`compounded`")

    def testCreate(self):
        """[Compound] Creating a compound record requires both keys provided"""
        compound = Compounded.Create(
            self.connection,
            {"first": 1, "second": 1, "message": "New compound key record"},
        )
        self.assertEqual(compound.key, (1, 1))

    def testLoadPrimary(self):
        Compounded.Create(
            self.connection, {"first": 12, "second": 42, "message": "Ahoi Ahoi"}
        )
        compound = Compounded.FromPrimary(self.connection, (12, 42))
        self.assertEqual(compound["message"], "Ahoi Ahoi")

    def testLoadWrongValueCount(self):
        """[Compound] Loading from primary requires the correct number of values"""
        self.assertRaises(TypeError, Compounded.FromPrimary, self.connection, 12)
        self.assertRaises(ValueError, Compounded.FromPrimary, self.connection, (1,))
        self.assertRaises(
            ValueError, Compounded.FromPrimary, self.connection, (1, 2, 3)
        )

    def testKeying(self):
        """[Compound] Compound record raises as expected in case of duplicate key"""
        Compounded.Create(
            self.connection, {"first": 1, "second": 1, "message": "very first"}
        )
        Compounded.Create(
            self.connection, {"first": 1, "second": 2, "message": "second messge"}
        )
        Compounded.Create(
            self.connection, {"first": 2, "second": 1, "message": "three is a charm"}
        )
        self.assertRaises(
            self.connection.IntegrityError,
            Compounded.Create,
            self.connection,
            {"first": 2, "second": 1, "message": "Break stuff"},
        )


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


class CookieTests(unittest.TestCase):
    def setUp(self):
        """Sets up the tests for the VersionedRecord class."""
        self.connection = CookieConnection()
        Session.autocommit(self.connection, True)

    def get_response_cookie_header(self):
        return self.connection.request_object.response.headers.setdefault(
            "Set-Cookie", {}
        )

    def testUncommittedCookie(self):
        Session.autocommit(self.connection, False)
        Session.Create(self.connection, "test_cookie")
        self.assertEqual(1, len(self.connection.uncommitted_cookies))
        # Validate that the Set-Cookie header is not actually set cause we didn't commit the cookie yet
        self.assertEqual(0, len(self.get_response_cookie_header()))

    def testAutocommitOnByDefault(self):
        Session.Create(self.connection, "test_cookie")
        self.assertEqual(0, len(self.connection.uncommitted_cookies))
        # This time it should be set because autocommit is the default action
        self.assertEqual(1, len(self.get_response_cookie_header()))

    def testManualCommit(self):
        Session.autocommit(self.connection, False)
        Session.Create(self.connection, "test_cookie")
        Session.commit(self.connection)
        self.assertEqual(0, len(self.connection.uncommitted_cookies))
        self.assertEqual(1, len(self.get_response_cookie_header()))

    def testRollback(self):
        Session.autocommit(self.connection, False)
        Session.Create(self.connection, "test_cookie")
        Session.rollback(self.connection)
        self.assertEqual(0, len(self.connection.uncommitted_cookies))
        # Cookie header should be empty after a rollback too!
        self.assertEqual(0, len(self.get_response_cookie_header()))

    def testMultipleCommits(self):
        Session.autocommit(self.connection, False)
        for i in range(5):
            Session.Create(self.connection, f"test_cookie{i}")

        self.assertEqual(5, len(self.connection.uncommitted_cookies))
        self.assertEqual(0, len(self.get_response_cookie_header()))

        Session.commit(self.connection)

        self.assertEqual(0, len(self.connection.uncommitted_cookies))
        self.assertEqual(5, len(self.get_response_cookie_header()))


class SecureCookieTest(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = CookieConnection()
        self.secure_cookie = SecureCookie(self.connection)

    def testTableName(self):
        """Validate that the SecureCookie class uses the correct name for the cookie."""

        class TestClass(SecureCookie):
            ...

        self.assertEqual("secureCookie", self.secure_cookie.TableName())
        self.assertEqual("testClass", TestClass(self.connection).TableName())

    def testCreateCookie(self):
        """Validate that the cookie is created and the values are the same."""
        data = {"key": "value"}

        self.secure_cookie.Create(self.connection, data)
        self.assertEqual(self.secure_cookie.rawcookie, data)

    def testCreateCookieAlternativeEncoder(self):
        """Validate that the cookie is created and the values are the same."""
        data = {"key": "value"}
        secure_cookie = SecureCookie(
            self.connection,
            encoder=CookieEncoder(cookie_hash=SupportedHashes.BLAKE2S),
        )
        
        # The Create method is a class method, so it doesnt know if we supplied a
        # different encoder. Pass the custom one we use to the method to decode the 
        # cookie correctly.
        SecureCookie.Create(
            self.connection,
            data,
            encoder=CookieEncoder(cookie_hash=SupportedHashes.BLAKE2S),
        )
        self.assertEqual(secure_cookie.rawcookie, data)

    def testUpdateCookie(self):
        """Validate that the values in the cookie are updated."""
        data = {"key": "value"}
        updated_data = {"key": "updated_value"}

        self.secure_cookie.Create(self.connection, data)
        self.assertEqual(self.secure_cookie.rawcookie, data)

        self.secure_cookie.Update(updated_data)
        self.assertEqual(self.secure_cookie.rawcookie, updated_data)

    def testDeleteCookie(self):
        """Ensure that the cookie is deleted and the header for deletion is passed
        to the response object."""
        data = {"key": "value"}

        self.secure_cookie.Create(self.connection, data)
        self.assertEqual(self.secure_cookie.rawcookie, data)

        self.secure_cookie.Delete()
        headers = self.connection.request_object.response.headers["Set-Cookie"]
        self.assertEqual(
            any("secureCookie=deleted;" in header for header in headers), True
        )

    def testValidateCookieHash(self):
        """Validate that the created cookie can be validated and decoded correctly."""
        data = {"key": "value"}
        hash = self.secure_cookie._CreateCookieHash(data)
        is_valid, cookie_data = self.secure_cookie._ValidateCookieHash(hash)

        self.assertTrue(is_valid)
        self.assertEqual(data, cookie_data)

    def testInvalidCookieHash(self):
        """Ensure that an invalid cookie hash does not pass the validation process."""
        data = {"key": "value"}
        self.secure_cookie._CreateCookieHash(data)
        is_valid, cookie_data = self.secure_cookie._ValidateCookieHash("someotherhash")

        self.assertFalse(is_valid)
        self.assertEqual(cookie_data, None)

    def testMissingCookie(self):
        """Validate that a missing cookie can not pass the validation process."""
        is_valid, cookie_data = self.secure_cookie._ValidateCookieHash("someotherhash")

        self.assertFalse(is_valid)
        self.assertEqual(cookie_data, None)

    def testTamperedCookie(self):
        """Validate that a tampered cookie can not pass the validation process."""
        data = {"key": "value"}
        self.secure_cookie.Create(self.connection, data)
        self.secure_cookie.cookies["secureCookie"] += "edited_hash"

        self.assertEqual(self.secure_cookie.rawcookie, None)
        self.assertTrue(self.secure_cookie.tampered)


def DatabaseConnection():
    """Returns an SQLTalk database connection to 'uWeb3_model_test'."""
    return mysql.Connect(
        host="localhost", user="stef", passwd="password", db="uweb_test", charset="utf8"
    )


def CookieConnection():
    req = request.Request(
        {
            "REQUEST_METHOD": "GET",
            "host": "localhost",
            "QUERY_STRING": "",
            "REMOTE_ADDR": "127.0.0.1",
            "PATH_INFO": "info",
        },
        None,
        None,
    )
    req.process_request()
    return safe_cookie.Connect(
        req,
        {},
        "secret",
    )


def SqliteConnection():
    path = os.path.join(Path().absolute(), "sqlite.db")
    return sqlite.Connect(path)


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
