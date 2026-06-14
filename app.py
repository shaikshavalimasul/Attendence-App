from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from flask import Flask
import mysql.connector
import cloudinary
import cloudinary.uploader
import qrcode
import io
import base64
import random
from datetime import datetime, timedelta

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

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
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
            return render_template('student-login.html', error="Invalid email or password")

    return render_template('student-login.html')


@app.route('/student-dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    return show_student_dashboard()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('student_login'))



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

    cursor.execute("""
        SELECT * FROM sessions
        WHERE teacher_id = %s AND is_active = TRUE AND end_time > NOW()
        ORDER BY session_id DESC LIMIT 1
    """, (session['teacher_id'],))
    active_session = cursor.fetchone()

    conn.close()

    qr_code = None
    if active_session:
        qr_data = f"session:{active_session[0]}"
        qr_code = generate_qr_base64(qr_data)

    return render_template('teacher_dashboard.html',
        name=teacher[2],
        unique_teacher_id=teacher[1],
        subject=teacher[5],
        department=teacher[6],
        active_session=active_session,
        qr_code=qr_code
    )


@app.route('/join-subject', methods=['POST'])
def join_subject():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    teacher_id_entered = request.form['teacher_id'].strip().upper()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teachers WHERE unique_teacher_id = %s", (teacher_id_entered,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
        return show_student_dashboard(message="Teacher ID not found. Please check and try again.", message_type="error")

    try:
        cursor.execute("""
            INSERT INTO student_teacher_mapping (student_id, teacher_id, subject, class_name, section)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['student_id'], teacher[0], teacher[5], teacher[6], ''))
        conn.commit()
        conn.close()
        return show_student_dashboard(message=f"Successfully joined {teacher[5]}!", message_type="success")

    except mysql.connector.IntegrityError:
        conn.close()
        return show_student_dashboard(message="You have already joined this subject.", message_type="error")

def show_student_dashboard(message=None, message_type=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE student_id = %s", (session['student_id'],))
    student = cursor.fetchone()

    cursor.execute("""
    SELECT teachers.subject, teachers.name, student_teacher_mapping.mapping_id
    FROM student_teacher_mapping
    JOIN teachers ON student_teacher_mapping.teacher_id = teachers.teacher_id
    WHERE student_teacher_mapping.student_id = %s
     """, (session['student_id'],))
    subjects = cursor.fetchall()
    conn.close()

    return render_template('student_dashboard.html',
        name=student[1],
        roll_number=student[2],
        class_name=student[3],
        section=student[4],
        subjects=subjects,
        message=message,
        message_type=message_type
    )

@app.route('/leave-subject', methods=['POST'])
def leave_subject():
    if 'student_id' not in session:
        return redirect(url_for('student-login'))

    mapping_id = request.form['mapping_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM student_teacher_mapping 
        WHERE mapping_id = %s AND student_id = %s
    """, (mapping_id, session['student_id']))
    conn.commit()
    conn.close()

    return show_student_dashboard(message="Subject removed.", message_type="success")



@app.route('/start-session', methods=['POST'])
def start_session():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    subject = request.form['subject']
    class_name = request.form['class_name']
    section = request.form['section']
    radius = request.form['radius']
    latitude = request.form['latitude']
    longitude = request.form['longitude']

    four_digit_code = str(random.randint(1000, 9999))

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=5)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (teacher_id, subject, class_name, section, session_date,
                               four_digit_code, radius_meters, teacher_latitude,
                               teacher_longitude, start_time, end_time, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (session['teacher_id'], subject, class_name, section, start_time.date(),
          four_digit_code, radius, latitude, longitude, start_time, end_time, True))
    conn.commit()
    conn.close()

    return redirect(url_for('teacher_dashboard'))


def generate_qr_base64(data):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data)
    qr.make()
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode('utf-8')



if __name__=='__main__':
    app.run(debug=True)