import unittest
from test.test_model.helpers import DatabaseConnection
from test.test_model.records import VersionedAuthor, VersionedBook


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


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
