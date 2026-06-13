import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
db = os.getenv("DB_NAME")

print("HOST:", repr(host))
print("PORT:", repr(port))
print("USER:", repr(user))
print("PASSWORD:", repr(password))
print("DB:", repr(db))

try:
    conn = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=db
    )

    if conn.is_connected():
        print("✅ Connected successfully!")
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        print("MySQL version:", cursor.fetchone())
        conn.close()

except mysql.connector.Error as e:
    print("❌ Connection failed:", e)