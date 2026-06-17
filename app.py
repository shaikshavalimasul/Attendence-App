from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from flask import Flask
import mysql.connector
import cloudinary
import cloudinary.uploader
import random
from datetime import datetime, timedelta
import requests as http_requests
import re
import math
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from flask import send_file
import csv
import io as io_module

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


@app.route('/debug-time')
def debug_time():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT NOW()")
    mysql_now = cursor.fetchone()[0]

    return f"""
    Python Time: {datetime.now()}<br>
    MySQL Time: {mysql_now}
    """


@app.route('/debug-session')
def debug_session():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, start_time, end_time, is_active
        FROM sessions
        ORDER BY session_id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    return f"""
    Python Now: {datetime.now()}<br>
    Session Start: {row[1]}<br>
    Session End: {row[2]}<br>
    Active: {row[3]}
    """

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
        print("Files Received:", request.files)
        print("Form received:", request.form)

        name = request.form['name']
        roll_number = request.form['roll_number']
        class_name = request.form['class_name']
        section = request.form['section']
        email = request.form['email']
        password = request.form['password']

        if 'photo' not in request.files or request.files['photo'].filename == '':
            return render_template('register.html', error="Please select a profile photo and try again.")

        photo = request.files['photo']
        hashed_password = generate_password_hash(password)

        upload_result = cloudinary.uploader.upload(photo)
        photo_url = upload_result['secure_url']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO students (name, roll_number, class_name, section, email, password, photo_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, roll_number, class_name, section, email, hashed_password, photo_url))
            conn.commit()
            conn.close()
            return redirect(url_for('student_login'))

        except mysql.connector.IntegrityError:
            conn.rollback()
            conn.close()
            return render_template('register.html', error=f"Email '{email}' is already registered. Please login instead.")

        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template('register.html', error=f"Something went wrong: {str(e)}")

    return render_template('register.html')


@app.route('/student_login', methods=['GET', 'POST'])
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
            return render_template('student_login.html', error="Invalid email or password")

    return render_template('student_login.html')


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

    if 'photo' not in request.files or request.files['photo'].filename == '':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers")
        teachers = cursor.fetchall()
        conn.close()
        return render_template('admin_dashboard.html', teachers=teachers, error="Please select a photo for the teacher.")

    photo = request.files['photo']
    upload_result = cloudinary.uploader.upload(photo)
    photo_url = upload_result['secure_url']

    hashed_password = generate_password_hash(password)
    unique_teacher_id = "TCH" + employee_id

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO teachers (unique_teacher_id, name, email, password, subject, department, employee_id, approved_by, photo_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (unique_teacher_id, name, email, hashed_password, subject, department, employee_id, session['admin_id'], photo_url))
        conn.commit()

        cursor.execute("SELECT * FROM teachers")
        teachers = cursor.fetchall()
        conn.close()
        return render_template('admin_dashboard.html', teachers=teachers, success=f"Teacher added! Unique ID: {unique_teacher_id}")

    except mysql.connector.IntegrityError as e:
        conn.rollback()
        cursor.execute("SELECT * FROM teachers")
        teachers = cursor.fetchall()
        conn.close()

        if 'unique_teacher_id' in str(e):
            error_msg = f"Employee ID '{employee_id}' is already used (Teacher ID '{unique_teacher_id}' exists). Please use a different Employee ID."
        elif 'email' in str(e):
            error_msg = f"Email '{email}' is already registered to another teacher."
        else:
            error_msg = "This teacher already exists."

        return render_template('admin_dashboard.html', teachers=teachers, error=error_msg)

    except Exception as e:
        conn.rollback()
        conn.close()
        return render_template('admin_dashboard.html', teachers=[], error=f"Something went wrong: {str(e)}")

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

    finalize_expired_sessions(session['teacher_id'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teachers WHERE teacher_id = %s", (session['teacher_id'],))
    teacher = cursor.fetchone()

    current_time = datetime.now()

    cursor.execute("""
        SELECT * FROM sessions
        WHERE teacher_id = %s AND is_active = TRUE AND end_time > %s
        ORDER BY session_id DESC LIMIT 1
    """, (session['teacher_id'], current_time))
    active_session = cursor.fetchone()

    print("current time:",current_time)
    print("Active Session=",active_session)

    session_attendance = []
    if active_session:
        cursor.execute("""
            SELECT students.name, students.roll_number, attendance.code_match,
                   attendance.location_match, attendance.face_match, attendance.ai_status
            FROM attendance
            JOIN students ON attendance.student_id = students.student_id
            WHERE attendance.session_id = %s
            ORDER BY attendance.submitted_at
        """, (active_session[0],))
        session_attendance = cursor.fetchall()

    conn.close()
    return render_template('teacher_dashboard.html',
        name=teacher[2],
        unique_teacher_id=teacher[1],
        subject=teacher[5],
        department=teacher[6],
        active_session=active_session,
        photo_path=teacher[11] if teacher[11] else "https://via.placeholder.com/140?text=Teacher",
        session_attendance=session_attendance
    )


@app.route('/join-subject', methods=['POST'])
def join_subject():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

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
    current_time = datetime.now()

    cursor.execute("""
        SELECT sessions.*, teachers.name
        FROM sessions
        JOIN student_teacher_mapping ON sessions.teacher_id = student_teacher_mapping.teacher_id
        JOIN teachers ON sessions.teacher_id = teachers.teacher_id
        WHERE student_teacher_mapping.student_id = %s
          AND sessions.is_active = TRUE
          AND sessions.end_time > %s
    """, (session['student_id'], current_time))
    active_sessions = cursor.fetchall()

    cursor.execute("""
    SELECT attendance.session_id, sessions.subject
    FROM attendance
    JOIN sessions ON attendance.session_id = sessions.session_id
    WHERE attendance.student_id = %s
      AND attendance.ai_status = 'Pending'
      AND attendance.face_match IS NULL
      AND sessions.end_time > %s
    """, (session['student_id'], current_time))
    pending_sessions = cursor.fetchall()


    cursor.execute("""
        SELECT teachers.subject, 
               COUNT(attendance.attendance_id) as total,
               SUM(CASE WHEN attendance.final_status = 'Present' THEN 1 ELSE 0 END) as present
        FROM attendance
        JOIN sessions ON attendance.session_id = sessions.session_id
        JOIN teachers ON sessions.teacher_id = teachers.teacher_id
        WHERE attendance.student_id = %s
        GROUP BY teachers.subject
    """, (session['student_id'],))
    percentage_data = cursor.fetchall()

    conn.close()

    return render_template('student_dashboard.html',
    name=student[1],
    roll_number=student[2],
    class_name=student[3],
    section=student[4],
    subjects=subjects,
    active_sessions=active_sessions,
    message=message,
    message_type=message_type,
    photo_path=student[7],
    pending_sessions=pending_sessions,
    percentage_data=percentage_data
)

@app.route('/leave-subject', methods=['POST'])
def leave_subject():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

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


@app.route('/submit-code', methods=['POST'])
def submit_code():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    session_id = request.form['session_id']
    entered_code = request.form['entered_code'].strip()
    student_lat = float(request.form['latitude'])
    student_lon = float(request.form['longitude'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
    session_row = cursor.fetchone()

    if not session_row:
        conn.close()
        return show_student_dashboard(message="Session not found.", message_type="error")

    actual_code = session_row[6]
    code_match = (entered_code == actual_code)

    teacher_lat = float(session_row[8])
    teacher_lon = float(session_row[9])
    allowed_radius = session_row[7]

    distance = calculate_distance(student_lat, student_lon, teacher_lat, teacher_lon)
    location_match = (distance <= allowed_radius)

    cursor.execute("""
        SELECT * FROM attendance 
        WHERE session_id = %s AND student_id = %s
    """, (session_id, session['student_id']))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return show_student_dashboard(message="You have already submitted attendance for this session.", message_type="error")

    if not code_match:
        conn.close()
        return show_student_dashboard(message="Incorrect code. Please try again.", message_type="error")

    if not location_match:
        # Location fail INSERT - change to:
        cursor.execute("""
        INSERT INTO attendance (session_id, student_id, code_match, location_match, ai_status, final_status)
        VALUES (%s, %s, %s, %s, %s, %s)
         """, (session_id, session['student_id'], code_match, location_match, 'Absent', 'Absent'))
        conn.commit()
        conn.close()
        return show_student_dashboard(
            message=f"Location check failed. You are {int(distance)}m away (must be within {allowed_radius}m).",
            message_type="error"
        )

    # Success INSERT - change to:
    cursor.execute("""
   INSERT INTO attendance (session_id, student_id, code_match, location_match, ai_status, final_status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (session_id, session['student_id'], code_match, location_match, 'Pending', 'Pending'))
    conn.commit()
    conn.close()

    return show_student_dashboard(message="Code and location verified! (Selfie verification coming next)", message_type="success")



def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371000  # meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = earth_radius * c
    return distance


@app.route('/verify-selfie', methods=['POST'])
def verify_selfie():
    if 'student_id' not in session:
        return {'success': False, 'message': 'Not logged in'}, 401

    data = request.get_json()
    session_id = data['session_id']
    selfie_data_url = data['selfie']

    base64_data = re.sub('^data:image/.+;base64,', '', selfie_data_url)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE student_id = %s", (session['student_id'],))
    student = cursor.fetchone()
    registered_photo_url = student[7]

    try:
        response = http_requests.post(
            "https://api-us.faceplusplus.com/facepp/v3/compare",
            data={
                "api_key": os.getenv("FACEPP_API_KEY"),
                "api_secret": os.getenv("FACEPP_API_SECRET"),
                "image_url1": registered_photo_url,
                "image_base64_2": base64_data
            }
        )
        result = response.json()

        if 'confidence' not in result:
            conn.close()
            return {'success': False, 'message': 'Face not detected. Please try again with better lighting.'}

        confidence = result['confidence']
        face_match = confidence >= 70
        final_status = 'Present' if face_match else 'Absent'

        cursor.execute("""
        UPDATE attendance 
        SET face_match = %s, ai_status = %s, final_status = %s, confirmed_at = %s
        WHERE session_id = %s AND student_id = %s
        """, (face_match, final_status, final_status, datetime.now(), session_id, session['student_id']))
        conn.commit()
        conn.close()

        if face_match:
            return {'success': True, 'message': f'Face verified ({confidence:.0f}% match)! Marked Present.'}
        else:
            return {'success': False, 'message': f'Face does not match ({confidence:.0f}% match). Marked Absent.'}

    except Exception as e:
        conn.rollback()
        conn.close()
        return {'success': False, 'message': f'Verification error: {str(e)}'}


@app.route('/profile')
def profile():
    if 'student_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (session['student_id'],))
        user = cursor.fetchone()
        conn.close()
        return render_template('profile.html',
            name=user[1], email=user[5], photo_path=user[7],
            back_url=url_for('student_dashboard'))

    if 'teacher_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers WHERE teacher_id = %s", (session['teacher_id'],))
        user = cursor.fetchone()
        conn.close()
        photo = user[11] if user[11] else "https://via.placeholder.com/140?text=Teacher"
        return render_template('profile.html',
            name=user[2], email=user[3], photo_path=photo,
            back_url=url_for('teacher_dashboard'))

    return redirect(url_for('home'))


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'student_id' not in session and 'teacher_id' not in session:
        return redirect(url_for('home'))

    name = request.form['name']
    email = request.form['email']

    print("Files Received:", request.files)

    photo_url = None
    if 'photo' in request.files:
        photo_file = request.files['photo']
        if photo_file.filename != '':
            upload_result = cloudinary.uploader.upload(photo_file)
            photo_url = upload_result['secure_url']
            print("New photo uploaded:", photo_url)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if 'student_id' in session:
            if photo_url:
                cursor.execute("UPDATE students SET name=%s, email=%s, photo_path=%s WHERE student_id=%s",
                                (name, email, photo_url, session['student_id']))
            else:
                cursor.execute("UPDATE students SET name=%s, email=%s WHERE student_id=%s",
                                (name, email, session['student_id']))
            conn.commit()
            conn.close()
            return redirect(url_for('student_dashboard'))

        if 'teacher_id' in session:
            if photo_url:
                cursor.execute("UPDATE teachers SET name=%s, email=%s, photo_path=%s WHERE teacher_id=%s",
                                (name, email, photo_url, session['teacher_id']))
            else:
                cursor.execute("UPDATE teachers SET name=%s, email=%s WHERE teacher_id=%s",
                                (name, email, session['teacher_id']))
            conn.commit()
            conn.close()
            return redirect(url_for('teacher_dashboard'))

    except mysql.connector.IntegrityError:
        conn.rollback()
        conn.close()
        return redirect(url_for('profile'))

    conn.close()
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()

        if role == 'student':
            cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM teachers WHERE email = %s", (email,))

        user = cursor.fetchone()
        conn.close()

        if not user:
            return render_template('forgot_password.html', error="No account found with this email.")

        if role == 'student':
            user_name = user[1]
            photo = user[7]
        else:
            user_name = user[2]
            photo = user[11] if user[11] else "https://via.placeholder.com/80?text=Photo"

        return render_template('forgot_password.html', user=user, user_name=user_name, photo=photo, role=role, email=email)

    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['POST'])
def reset_password():
    role = request.form['role']
    email = request.form['email']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        conn = get_db_connection()
        cursor = conn.cursor()
        if role == 'student':
            cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM teachers WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if role == 'student':
            user_name, photo = user[1], user[7]
        else:
            user_name = user[2]
            photo = user[11] if user[11] else "https://via.placeholder.com/80?text=Photo"

        return render_template('forgot_password.html', user=user, user_name=user_name, photo=photo, role=role, email=email, error="Passwords do not match.")

    hashed_password = generate_password_hash(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()
    if role == 'student':
        cursor.execute("UPDATE students SET password=%s WHERE email=%s", (hashed_password, email))
    else:
        cursor.execute("UPDATE teachers SET password=%s WHERE email=%s", (hashed_password, email))
    conn.commit()
    conn.close()

    if role == 'student':
        return redirect(url_for('student_login'))
    else:
        return redirect(url_for('teacher_login'))


@app.route('/delete-teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM student_teacher_mapping WHERE teacher_id = %s", (teacher_id,))
        cursor.execute("DELETE FROM attendance WHERE session_id IN (SELECT session_id FROM sessions WHERE teacher_id = %s)", (teacher_id,))
        cursor.execute("DELETE FROM sessions WHERE teacher_id = %s", (teacher_id,))
        cursor.execute("DELETE FROM subject_attendance_summary WHERE teacher_id = %s", (teacher_id,))
        cursor.execute("DELETE FROM teachers WHERE teacher_id = %s", (teacher_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        conn.rollback()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    


def finalize_expired_sessions(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    current_time = datetime.now()

    cursor.execute("""
        SELECT session_id FROM sessions 
        WHERE teacher_id = %s AND end_time <= %s AND is_active = TRUE
    """, (teacher_id, current_time))
    expired_sessions = cursor.fetchall()

    for (session_id,) in expired_sessions:
        cursor.execute("""
            SELECT student_id FROM student_teacher_mapping WHERE teacher_id = %s
        """, (teacher_id,))
        all_students = cursor.fetchall()

        for (student_id,) in all_students:
            cursor.execute("""
                SELECT * FROM attendance WHERE session_id = %s AND student_id = %s
            """, (session_id, student_id))
            existing = cursor.fetchone()

            if not existing:
                cursor.execute("""
                    INSERT INTO attendance (session_id, student_id, ai_status, final_status, confirmed_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session_id, student_id, 'Absent', 'Absent', current_time))

        cursor.execute("UPDATE sessions SET is_active = FALSE WHERE session_id = %s", (session_id,))

    conn.commit()
    conn.close()  


@app.route('/session-review')
@app.route('/session-review/<int:session_id>')
def session_review(session_id=None):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM sessions WHERE teacher_id = %s ORDER BY session_id DESC
    """, (session['teacher_id'],))
    sessions_list = cursor.fetchall()

    if session_id is None:
        conn.close()
        return render_template('session_review.html', sessions_list=sessions_list, selected_session=None)

    cursor.execute("SELECT * FROM sessions WHERE session_id = %s AND teacher_id = %s", (session_id, session['teacher_id']))
    selected_session = cursor.fetchone()

    if not selected_session:
        conn.close()
        return redirect(url_for('session_review'))

    cursor.execute("""
        SELECT students.name, students.roll_number, attendance.attendance_id, attendance.final_status
        FROM attendance
        JOIN students ON attendance.student_id = students.student_id
        WHERE attendance.session_id = %s
        ORDER BY students.roll_number
    """, (session_id,))
    attendance_rows = cursor.fetchall()
    conn.close()

    total_students = len(attendance_rows)
    present_count = sum(1 for row in attendance_rows if row[3] == 'Present')
    absent_count = total_students - present_count
    percentage = round((present_count / total_students * 100), 1) if total_students > 0 else 0

    return render_template('session_review.html',
        sessions_list=sessions_list,
        selected_session=selected_session,
        attendance_rows=attendance_rows,
        total_students=total_students,
        present_count=present_count,
        absent_count=absent_count,
        percentage=percentage
    )


@app.route('/confirm-attendance/<int:session_id>', methods=['POST'])
def confirm_attendance(session_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    for key in request.form:
        if key.startswith('status_'):
            attendance_id = key.replace('status_', '')
            new_status = request.form[key]
            reason = request.form.get('reason_' + attendance_id, '')

            cursor.execute("SELECT ai_status, final_status FROM attendance WHERE attendance_id = %s", (attendance_id,))
            row = cursor.fetchone()

            is_edited = (row[1] != new_status) if row else False

            cursor.execute("""
                UPDATE attendance 
                SET final_status = %s, is_manually_edited = %s, edit_reason = %s, confirmed_at = %s
                WHERE attendance_id = %s
            """, (new_status, is_edited, reason if reason else None, datetime.now(), attendance_id))

    conn.commit()
    conn.close()

    return redirect(url_for('session_review', session_id=session_id))

def get_session_data(session_id, teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions WHERE session_id = %s AND teacher_id = %s", (session_id, teacher_id))
    sess = cursor.fetchone()

    cursor.execute("""
        SELECT students.name, students.roll_number, attendance.final_status, 
               attendance.is_manually_edited, attendance.edit_reason
        FROM attendance
        JOIN students ON attendance.student_id = students.student_id
        WHERE attendance.session_id = %s
        ORDER BY students.roll_number
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()

    return sess, rows


@app.route('/download-summary/<int:session_id>/<filetype>')
def download_summary(session_id, filetype):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    sess, rows = get_session_data(session_id, session['teacher_id'])
    if not sess:
        return redirect(url_for('session_review'))

    present = [r for r in rows if r[2] == 'Present']
    absent = [r for r in rows if r[2] == 'Absent']

    show_list = absent if len(absent) <= len(present) else present
    list_label = "ABSENT" if len(absent) <= len(present) else "PRESENT"

    if filetype == 'csv':
        output = io_module.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Attendance Summary'])
        writer.writerow(['Subject', sess[2]])
        writer.writerow(['Class', f"{sess[3]}-{sess[4]}"])
        writer.writerow(['Date', str(sess[5])])
        writer.writerow(['Total Students', len(rows)])
        writer.writerow(['Present', len(present)])
        writer.writerow(['Absent', len(absent)])
        writer.writerow([])
        writer.writerow([f'{list_label} STUDENTS'])
        writer.writerow(['Roll Number', 'Name'])
        for r in show_list:
            writer.writerow([r[1], r[0]])

        mem = io_module.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=f'summary_{session_id}.csv')

    else:
        buffer = io_module.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Attendance Summary")
        c.setFont("Helvetica", 11)
        c.drawString(50, 720, f"Subject: {sess[2]}")
        c.drawString(50, 700, f"Class: {sess[3]}-{sess[4]}")
        c.drawString(50, 680, f"Date: {sess[5]}")
        c.drawString(50, 660, f"Total: {len(rows)}  Present: {len(present)}  Absent: {len(absent)}")
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, 630, f"{list_label} STUDENTS")
        c.setFont("Helvetica", 11)
        y = 605
        for r in show_list:
            c.drawString(50, y, f"Roll {r[1]} - {r[0]}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'summary_{session_id}.pdf')


@app.route('/download-complete/<int:session_id>/<filetype>')
def download_complete(session_id, filetype):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    sess, rows = get_session_data(session_id, session['teacher_id'])
    if not sess:
        return redirect(url_for('session_review'))

    present_count = sum(1 for r in rows if r[2] == 'Present')

    if filetype == 'csv':
        output = io_module.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Complete Attendance Record'])
        writer.writerow(['Subject', sess[2]])
        writer.writerow(['Class', f"{sess[3]}-{sess[4]}"])
        writer.writerow(['Date', str(sess[5])])
        writer.writerow(['Total', len(rows), 'Present', present_count, 'Absent', len(rows) - present_count])
        writer.writerow([])
        writer.writerow(['Roll Number', 'Name', 'Status', 'Manually Edited', 'Reason'])
        for r in rows:
            writer.writerow([r[1], r[0], r[2], 'Yes' if r[3] else 'No', r[4] or '-'])

        mem = io_module.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=f'complete_{session_id}.csv')

    else:
        buffer = io_module.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Complete Attendance Record")
        c.setFont("Helvetica", 11)
        c.drawString(50, 720, f"Subject: {sess[2]}  Class: {sess[3]}-{sess[4]}  Date: {sess[5]}")
        c.drawString(50, 700, f"Total: {len(rows)}  Present: {present_count}  Absent: {len(rows) - present_count}")
        y = 670
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Roll No")
        c.drawString(110, y, "Name")
        c.drawString(280, y, "Status")
        c.drawString(350, y, "Edited")
        c.drawString(420, y, "Reason")
        y -= 18
        c.setFont("Helvetica", 9)
        for r in rows:
            c.drawString(50, y, str(r[1]))
            c.drawString(110, y, str(r[0])[:25])
            c.drawString(280, y, r[2])
            c.drawString(350, y, 'Yes' if r[3] else 'No')
            c.drawString(420, y, (r[4] or '-')[:20])
            y -= 16
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'complete_{session_id}.pdf')


if __name__=='__main__':
    app.run(debug=False)