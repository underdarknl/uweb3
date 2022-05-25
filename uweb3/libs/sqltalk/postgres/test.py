from uweb3.libs.sqltalk import postgres

con = postgres.Connect(
    host="localhost", database="test", user="stef", password="password"
)

with con as cursor:
    # res = cursor.Execute("select * from test")
    res = cursor.Select(
        "test",
        conditions="test='t'",
        group=("test=t",),
    )
    print(res[0])
