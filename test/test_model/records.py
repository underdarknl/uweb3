from uweb3 import model


class BasicTestRecord(model.Record):
    """Test record for offline tests."""


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


class BasicTestRecordSqlite(model.Record):
    """Test record for offline tests."""

    _CONNECTOR = "sqlite"
