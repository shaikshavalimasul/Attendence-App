from flask import Flask
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.route('/')
def home():
    return "Flask is connected to Mysql !"

@app.route('/add-test-student')
def add_test_student():
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("""
                   Insert into students (name,roll_number,class_name,section,email,password)
                   values (%s,%s,%s,%s,%s,%s)
                   """,("Rahul","101","CSE-A","A","rahul@test.com","test123"))
    conn.commit()
    conn.close()
    return "Test student added!"

@app.route('/show-students')
def show_students():
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM students")
    students=cursor.fetchall()
    conn.close()
    return str(students)


if __name__=='__main__':
    app.run(debug=True)