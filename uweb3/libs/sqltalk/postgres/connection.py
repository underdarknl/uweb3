__author__ = "Stef van Houten <stef@underdark.nl>"
__version__ = "0.1"

import logging
from re import I
import psycopg2
import psycopg2.extras
import psycopg2.extensions

from .. import sqlresult
from . import cursor
import psycopg2.sql


class BaseConnection:
    _CONNECTOR = None

    def __init__(self, dbname, debug):
        self.queries = []
        # self.logger = logging.getLogger(f'{self._CONNECTOR}_{dbname}')
        self.logger = logging.getLogger("testlogger")

        # TODO remove below console debugger
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        # TODO remove above

        if debug:
            self.debug = True
            self.logger.setLevel(logging.DEBUG)
        else:
            self.debug = False
            self.logger.setLevel(logging.WARNING)


class Connection(psycopg2.extensions.connection, BaseConnection):
    _CONNECTOR = "postgres"

    def __init__(self, dbname, *args, **kwargs):
        super().__init__(dbname, *args, **kwargs)
        BaseConnection.__init__(self, dbname, True)

    def __enter__(self) -> cursor.Cursor:
        self.cur = self.cursor()
        return self.cur  # type: ignore

    def __exit__(self, exc_type, exc_value, _exc_traceback):
        self.commit()
        self.cur.close()

    # def commit(self):
    #   self.commit()

    # def rollback(self):
    #   self.rollback()

    # def autocommit(self, value):
    #   self.autocommit = value
    def EscapeValues(self, obj):
        return obj

    def EscapeField(self, field, multiple=False):
        """Returns a SQL escaped field or table name."""
        if not field:
            return psycopg2.sql.SQL("*")
        if isinstance(field, str):
            res = psycopg2.sql.SQL("{field}").format(
                field=psycopg2.sql.Identifier(field)
            )
            return res
        elif not multiple and isinstance(field, tuple):
            return psycopg2.sql.SQL("{field_one} as {field_two}").format(
                field_one=psycopg2.sql.Identifier(field[0]),
                field_two=psycopg2.sql.Identifier(field[1]),
            )
        return psycopg2.sql.SQL("{fields}").format(
            fields=psycopg2.sql.SQL(", ").join(
                [psycopg2.sql.Identifier(f) for f in field]
            )
        )

    def CurrentDatabase(self):
        """Return the name of the currently used database"""
        return self.Query("SELECT current_database()")[0]["current_database"]  # type: ignore

    def Query(self, query_string, cur=None, values=None):
        if not cur:
            cur = self.cursor()
        results = None

        if values:
            cur.execute(query_string, values)
        else:
            cur.execute(query_string)

        if cur.description:
            results = cur.fetchall()

        if results:
            fields = list(results[0])
        else:
            fields = []
        return sqlresult.ResultSet(
            affected=cur.rowcount,
            fields=fields,
            charset=self.encoding,
            insertid=cur.lastrowid,
            query=query_string,
            result=results,
        )

    def Info(self):
        return {
            "db": self.CurrentDatabase(),
            "charset": self.encoding,
            "server": self.server_version,
            # 'debug': self.debug,
            "autocommit": self.autocommit,
            # 'querycount': self.counter_queries,
            # 'transactioncount': self.counter_transactions
        }

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
