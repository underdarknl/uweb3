#!/usr/bin/python
"""SQLTalk MySQL Cursor class."""
__author__ = "Elmer de Looff <elmer@underdark.nl>"
__version__ = "0.13"

# Standard modules
import warnings
import weakref

import pymysql

from ..base_cursor import BaseCursor


class ReturnObject(tuple):
    """An object that functions as a tuple but has more required attributes."""

    def __new__(cls, connection, results):
        """Creates the immutable tuple."""
        return super().__new__(cls, tuple(results))

    def __init__(self, connection, results):
        """Adds the required attributes."""
        if connection._result is not None:
            self.insertid = connection._result.insert_id
        else:
            self.insertid = None


class Cursor(pymysql.cursors.DictCursor, BaseCursor):
    """Cursor to execute database interaction with, within a transaction."""

    def __init__(self, connection):
        self.description = None
        self.rownumber = 0
        self.rowcount = -1
        self.arraysize = 1
        self._executed = None
        self._result = None
        self._rows = None
        self._warnings_handled = False
        self._connection = weakref.ref(connection)

    def Describe(self, table, field=""):
        """Describe table in database or field in table.

        Takes
          table: string. Name of the table to describe.
          field: string (optional). Field name to describe.

        Returns:
          sqlresult.ResultSet object.
        """
        return self._Execute(
            "DESC %s %s"
            % (
                self._StringTable(table, self.connection.EscapeField),
                self._StringFields(field, self.connection.EscapeField),
            )
        )

    def Execute(self, query):
        """Executes a raw query."""
        return self._Execute(query)

    def NoEscapeField(self, field, multiple=False):
        """Returns a SQL unescaped field or table name.

        Set multiple = True if field is a tuple of names to be returned.
        If multiple = False, and a tuple is encountered `field` as `name` will be
          returned where the second part of the tuple is the `name` part.
        """
        if not field:
            return ""
        if isinstance(field, str):
            return field
        elif not multiple and isinstance(field, tuple):
            return "%s as %s" % (field[0], field[1])
        return map(self.NoEscapeField, field)

    def SelectTables(self, contains=None, exact=False):
        """Returns table names from the current database.

        Arguments
          % contains: str ~~ ''
            A substring required to be present in all returned table names.
          % exact: bool ~~ False
            Flags whether the string given in contains should be the exact name.

        Returns:
          set: tables names that match the filter.
        """
        if contains:
            contains = self.connection.EscapeValues(contains)
            if exact:
                result = self._Execute("SHOW TABLES LIKE %s" % contains)
            else:
                # Strip quotes from escaped string to allow insertion of wildcards.
                result = self._Execute(
                    'SHOW TABLES LIKE "%%%s%%"' % (contains.strip("'"))
                )
        else:
            result = self._Execute("SHOW TABLES")
        return set(result[result.fieldnames[0]])

    def Truncate(self, table):
        """Truncate table in database, reducing it to 0 rows.

        Arguments:
          table: string, name of the table to truncate.

        Returns:
          sqlresult.ResultSet object.
        """
        return self._Execute(
            "TRUNCATE %s" % (self._StringTable(table, self.connection.EscapeField))
        )

    def _ProcessWarnings(self, resultset):
        """Updates messages attribute with warnings given by the MySQL server."""
        db_warnings = self.connection.ShowWarnings()
        if db_warnings:
            # This is done in two loops in case Warnings are set to raise exceptions.
            for warning in db_warnings:
                self.connection.logger.warning(
                    "%d: %s\nQuery: %s", warning[1], warning[2], resultset.query
                )
                resultset.warnings.append(warning)
            for warning in db_warnings:
                warnings.warn(warning[-1], self.Warning, 3)

    @property
    def connection(self):
        """Returns the connection that this cursor belongs to."""
        connection = self._connection()
        if connection is None:
            raise self.ProgrammingError("Connection for this cursor closed.")
        return connection

    DatabaseError = pymysql.DatabaseError
    DataError = pymysql.DataError
    Error = pymysql.Error
    IntegrityError = pymysql.IntegrityError
    InterfaceError = pymysql.InterfaceError
    InternalError = pymysql.InternalError
    NotSupportedError = pymysql.NotSupportedError
    OperationalError = pymysql.OperationalError
    ProgrammingError = pymysql.ProgrammingError
    Warning = pymysql.Warning
