"""Model for the uweb3 test server"""

from uweb3 import model


class SignedExample(model.SecureCookie):
    """Model for the Singed Cookie example"""


class Fish(model.Record):
    """Model for the Sqlite example"""

    _CONNECTOR = "sqlite"

    @classmethod
    def create_table(cls, connection):
        with connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS fish")
            cursor.Execute("DROP TABLE IF EXISTS tank")
            cursor.Execute(
                "CREATE TABLE fish(ID INTEGER, name TEXT, species TEXT, tank INTEGER)"
            )
            cursor.Execute("CREATE TABLE tank(ID INTEGER, name TEXT)")
            cursor.Execute(
                """INSERT INTO tank(ID, name) VALUES (1, "Living Room sqlite")"""
            )
            cursor.Execute(
                """INSERT INTO fish(ID, name, species, tank) VALUES (1, "sammy", "shark", 1)"""
            )


class Tank(model.Record):
    """Model for the Mysql example"""

    @classmethod
    def create_table(cls, connection):
        with connection as cursor:
            cursor.Execute("DROP TABLE IF EXISTS tank")
            cursor.Execute(
                """
                CREATE TABLE `tank` (
                `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
                `name` varchar(45) DEFAULT NULL,
                PRIMARY KEY (`ID`)
                )
                """
            )
            cursor.Execute(
                "INSERT INTO `tank` VALUES (1,'Living Room'),(2,'Squid Tank');"
            )


class Posts(model.Record):
    """Model for the Mysql example"""

    _CONNECTOR = "restfulljson"


class Albums(model.Record):
    """Model for the Mysql example"""

    _CONNECTOR = "restfulljson"
