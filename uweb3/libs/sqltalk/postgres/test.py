from uweb3.libs.sqltalk import postgres

con = postgres.Connect(
    host="localhost", database="test", user="stef", password="password"
)

with con as cursor:
    # res = cursor.Execute("select * from test")
    # res = cursor.Select("test", fields=("test",))
    cursor.Insert("test", {"test": "test"})
    print(res[0])
