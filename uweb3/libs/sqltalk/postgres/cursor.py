#!/usr/bin/python
"""PostgreSQL Cursor class."""
__author__ = "Stef van Houten <stef@underdark.nl>"
__version__ = "0.1"

from re import T
import weakref
import psycopg2
import psycopg2.extras
import psycopg2.extensions
import psycopg2.sql

from uweb3.libs.sqltalk import base_cursor

from abc import ABC, abstractmethod


class AbstractCursor(ABC):
    """Abstract class the required structure for a cursor class."""

    @abstractmethod
    def Execute(self, query, cur=None):
        pass


class Cursor(psycopg2.extras.RealDictCursor, base_cursor.BaseCursor):
    def __init__(self, connection, *args, **kwargs):
        super().__init__(connection, *args, **kwargs)
        self._connection = weakref.ref(connection)

    def _Execute(self, query):
        """Actually executes the query and returns the result of it.

        Arguments:
          @ query: basestring,
            Fully formatted sql statement to execute. In case of unicode, the
            string is encoded to the local character set before it is passed on
            to the server.

        Returns:
          sqlresult.ResultSet instance holding all query result data.
        """

        # self._LogQuery(query)
        return self.connection.Query(query)

    def Execute(self, query):
        """Executes a raw query."""
        return self._Execute(query)

    def Select(
        self,
        table,
        fields=None,
        conditions=None,
        order=None,
        group=None,
        limit=None,
        offset=0,
        escape=True,
        totalcount=False,
        distinct=False,
    ):
        """Select fields from table that match the conditions, ordered and limited.

        Arguments:
          table:      string/list/tuple. Table(s) to select fields out of.
          fields:     string/list/tuple (optional). Fields to select. Default '*'.
                      As string, single field name. (autoquoted)
                      As list/tuple, one field name per element. (autoquoted)
                      If the fielname itself is supplied as a tuple,
                      `field` as `name' will be returned where name is the second
                      item in the tuple. (autoquoted)
          conditions: string/list/tuple (optional). SQL 'where' statement.
                      Literal as string. AND'd if list/tuple.
                      THESE WILL NOT BE ESCAPED FOR YOU, EVER.
          order:      (nested) list/tuple (optional).
                      Defines sorting of table before updating, elements can be:
                        string: a field to order by (in default database order).
                        list/tuple of two elements:
                          1) string, field name to order by
                          2) bool, revserse; set this to True to reverse the order
          group:      str (optional). Field name or function to group result by.
          limit:      integer (optional). Defines output size in rows.
          offset:     integer (optional). Number of rows to skip, requires limit.
          escape:     boolean. Defines whether table and field names should be
                      escaped. Set this to False if you want to make use of MySQL
                      functions on this query. Default True.
          totalcount: boolean. If this is set to True, queries with a LIMIT applied
                      will have the full number of matching rows on
                      the affected_rows attribute of the resultset.
          distinct:   bool (optional). Performs a DISTINCT query if set to True.

        Returns:
          sqlresult.ResultSet object.
        """
        field_escape = self.connection.EscapeField if escape else self.NoEscapeField

        test = "SELECT"
        if totalcount and limit is not None:
            test += " SQL_CALC_FOUND_ROWS "
        if distinct:
            test += " DISTINCT "

        if fields:
            fields = psycopg2.sql.SQL(",").join(
                [psycopg2.sql.Identifier(field) for field in fields]
            )
        else:
            fields = psycopg2.sql.SQL("*")

        if conditions:
            conditions = psycopg2.sql.SQL("WHERE ") + psycopg2.sql.SQL(
                self._StringConditions(conditions, field_escape)
            )
        else:
            conditions = psycopg2.sql.SQL("")

        if group:
            group = psycopg2.sql.SQL(self._StringGroup(group, field_escape))
        else:
            group = psycopg2.sql.SQL("")

        if order:
            order = psycopg2.sql.SQL(self._StringOrder(order, field_escape))
        else:
            order = psycopg2.sql.SQL("")

        if limit:
            limit = psycopg2.sql.SQL(self._StringLimit(limit, offset))
        else:
            limit = psycopg2.sql.SQL("")

        query = psycopg2.sql.SQL(
            "SELECT {fields} FROM {table} {conditions} {group}"
        ).format(
            fields=fields,
            table=psycopg2.sql.Identifier(table),
            conditions=conditions,
            group=group,
            order=order,
            limit=limit,
        )
        result = self._Execute(query)
        # if totalcount and limit is not None:
        #   result.affected = self._Execute('SELECT FOUND_ROWS()')[0][0]
        return result

    Error = psycopg2.Error
    InterfaceError = psycopg2.InterfaceError
    DatabaseError = psycopg2.DatabaseError
    DataError = psycopg2.DataError
    OperationalError = psycopg2.OperationalError
    IntegrityError = psycopg2.IntegrityError
    InternalError = psycopg2.InternalError
    ProgrammingError = psycopg2.ProgrammingError
    NotSupportedError = psycopg2.NotSupportedError
    Warning = psycopg2.Warning
