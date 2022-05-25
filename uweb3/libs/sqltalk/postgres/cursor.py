#!/usr/bin/python
"""PostgreSQL Cursor class."""
__author__ = "Stef van Houten <stef@underdark.nl>"
__version__ = "0.1"

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

    def _Execute(self, sql, args):
        """Actually executes the query and returns the result of it.

        Arguments:
          @ query: basestring,
            Fully formatted sql statement to execute. In case of unicode, the
            string is encoded to the local character set before it is passed on
            to the server.

        Returns:
          sqlresult.ResultSet instance holding all query result data.
        """
        # if args:
        #   self._LogQuery(sql % args)
        # else:
        #   self._LogQuery(sql)
        return self.connection.Query(sql.strip(), args, self)

    def Execute(self, query, replacements=None):
        """Executes a raw query."""
        return self._Execute(query, replacements)

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
        sql = "SELECT %s %s %s FROM %s WHERE %s %s %s %s"

        test = "SELECT"
        if totalcount and limit is not None:
            test += " SQL_CALC_FOUND_ROWS "
        if distinct:
            test += " DISTINCT "

        fields = self._StringFields(fields, field_escape)
        table = self._StringTable(table, field_escape)
        conditions = self._StringConditions(group, field_escape)
        group = self._StringGroup(group, field_escape)
        order = self._StringOrder(order, field_escape)
        limit = self._StringLimit(limit, offset)

        # TODO: Add escaping for sql
        psycopg2.sql.SQL("SELECT {fields} FROM {table} ").format()

        result = self._Execute(test, replacements)
        # if totalcount and limit is not None:
        #   result.affected = self._Execute('SELECT FOUND_ROWS()')[0][0]
        return result

    @staticmethod
    def _StringConditions(conditions, _unused_field_escape):
        if not conditions:
            return "1=1"
        elif not isinstance(conditions, str):
            return " AND ".join(conditions)
        return conditions
