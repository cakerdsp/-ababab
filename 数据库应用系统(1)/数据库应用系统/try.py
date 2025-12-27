import psycopg2
connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
    )
cur = connection.cursor()


login = '22320021'
cur.execute('''SELECT "Status" FROM myapp_order WHERE "OID" = %s;''', ['123'])
status = cur.fetchall()
print(status[0][0])

# 关闭连接
connection.close()