import unittest
from test.test_model.helpers import DatabaseConnection
from test.test_model.records import Author, BasicTestRecord, Book, Compounded

from uweb3 import model


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


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
