import unittest
from test.test_model.helpers import CookieConnection
from test.test_model.records import Session

from uweb3.model import CookieHasher, SecureCookie, SupportedHashes


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
            encoder=CookieHasher(cookie_hash=SupportedHashes.BLAKE2S),
        )

        # The Create method is a class method, so it doesnt know if we supplied a
        # different encoder. Pass the custom one we use to the method to decode the
        # cookie correctly.
        SecureCookie.Create(
            self.connection,
            data,
            encoder=CookieHasher(cookie_hash=SupportedHashes.BLAKE2S),
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
        is_valid, cookie_data, deprecated = self.secure_cookie._ValidateCookieHash(hash)

        self.assertTrue(is_valid)
        self.assertEqual(data, cookie_data)

    def testInvalidCookieHash(self):
        """Ensure that an invalid cookie hash does not pass the validation process."""
        data = {"key": "value"}
        self.secure_cookie._CreateCookieHash(data)
        is_valid, cookie_data, deprecated = self.secure_cookie._ValidateCookieHash(
            "someotherhash"
        )

        self.assertFalse(is_valid)
        self.assertEqual(cookie_data, None)

    def testMissingCookie(self):
        """Validate that a missing cookie can not pass the validation process."""
        is_valid, cookie_data, deprecated = self.secure_cookie._ValidateCookieHash(
            "someotherhash"
        )

        self.assertFalse(is_valid)
        self.assertEqual(cookie_data, None)

    def testTamperedCookie(self):
        """Validate that a tampered cookie can not pass the validation process."""
        data = {"key": "value"}
        self.secure_cookie.Create(self.connection, data)
        self.secure_cookie.cookies["secureCookie"] += "edited_hash"

        self.assertEqual(self.secure_cookie.rawcookie, None)
        self.assertTrue(self.secure_cookie.tampered)

    def testDeprecatedHasher(self):
        """Validate that a deprecated hasher is not used and instead a non depricated
        hasher is used."""
        secure_cookie = SecureCookie(
            self.connection,
            encoder=CookieHasher(cookie_hash=SupportedHashes.RIPEMD160),
        )
        SecureCookie.Create(
            self.connection,
            "test_deprecated_cookie",
            encoder=CookieHasher(cookie_hash=SupportedHashes.RIPEMD160),
        )

        self.assertNotIn(
            SupportedHashes.RIPEMD160.value.prefix,
            secure_cookie.cookies["secureCookie"],
        )


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
