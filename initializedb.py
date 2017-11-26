import psycopg2

def initialize():
    conn = psycopg2.connect(database = "logindb", user = "postgres", password = "pass123", host = "127.0.0.1", port = "5432")
    print("Opened database successfully")

    cur = conn.cursor()

    cur.execute("UPDATE LOGIN SET state = 'offline' WHERE state != 'offline';")
    conn.commit()

    print("Operation done successfully")
    conn.close()
