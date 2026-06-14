from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from flask import Flask
import mysql.connector
import cloudinary
import cloudinary.uploader

from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

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
    return render_template('home.html')

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


app.config['UPLOAD_FOLDER'] = 'static/uploads'

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        class_name = request.form['class_name']
        section = request.form['section']
        email = request.form['email']
        password = request.form['password']
        photo = request.files['photo']

        hashed_password = generate_password_hash(password)

        # Upload to Cloudinary instead of local disk
        upload_result = cloudinary.uploader.upload(photo)
        photo_url = upload_result['secure_url']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (name, roll_number, class_name, section, email, password, photo_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, roll_number, class_name, section, email, hashed_password, photo_url))
        conn.commit()
        conn.close()

        return "Registration successful!"

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
        student = cursor.fetchone()
        conn.close()

        if student and check_password_hash(student[6], password):
            session['student_id'] = student[0]
            session['name'] = student[1]
            return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password")

    return render_template('login.html')


@app.route('/student-dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = %s", (session['student_id'],))
    student = cursor.fetchone()
    conn.close()

    return render_template('student_dashboard.html',
        name=student[1],
        roll_number=student[2],
        class_name=student[3],
        section=student[4],
        email=student[5]
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        admin_user = cursor.fetchone()
        conn.close()

        if admin_user and (admin_user[3]==password):
            session['admin_id'] = admin_user[0]
            session['admin_name'] = admin_user[1]
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid email or password")

    return render_template('admin_login.html')


@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers")
    teachers = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', teachers=teachers)


@app.route('/add-teacher', methods=['POST'])
def add_teacher():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    name = request.form['name']
    subject = request.form['subject']
    department = request.form['department']
    employee_id = request.form['employee_id']
    email = request.form['email']
    password = request.form['password']

    hashed_password = generate_password_hash(password)
    unique_teacher_id = "TCH" + employee_id

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO teachers (unique_teacher_id, name, email, password, subject, department, employee_id, approved_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (unique_teacher_id, name, email, hashed_password, subject, department, employee_id, session['admin_id']))
    conn.commit()

    cursor.execute("SELECT * FROM teachers")
    teachers = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', teachers=teachers, success=f"Teacher added! Unique ID: {unique_teacher_id}")


@app.route('/teacher-login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers WHERE email = %s", (email,))
        teacher = cursor.fetchone()
        conn.close()

        if teacher and check_password_hash(teacher[4], password):
            session['teacher_id'] = teacher[0]
            session['teacher_name'] = teacher[2]
            return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('teacher_login.html', error="Invalid email or password")

    return render_template('teacher_login.html')


@app.route('/teacher-dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers WHERE teacher_id = %s", (session['teacher_id'],))
    teacher = cursor.fetchone()
    conn.close()

    return render_template('teacher_dashboard.html',
        name=teacher[2],
        unique_teacher_id=teacher[1],
        subject=teacher[5],
        department=teacher[6]
    )


if __name__=='__main__':
    app.run(debug=True)