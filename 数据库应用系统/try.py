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
cur.execute('''INSERT INTO myapp_order VALUES('121334','配置','1998-1-1',100,'22320021','321')''')
status = cur.fetchall()
print(status[0][0])

# 关闭连接
connection.close()