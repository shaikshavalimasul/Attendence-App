# Smart Attendance System

An AI-powered web application that automates classroom attendance using face recognition, GPS location verification, and time-bound session codes — reducing attendance time from 10-15 minutes to under a minute per class.

## Problem It Solves

Traditional attendance in large classrooms (50-100+ students) requires calling out roll numbers one by one, wasting significant class time every session. This system lets teachers start a verified attendance session in seconds, while students confirm their presence through a three-layer security check that prevents proxy attendance.

## Features

- **Role-based access control** — Admin, Teacher, and Student roles with separate permissions
- **Admin-approved teacher onboarding** — Principal adds teachers and generates unique IDs
- **Three-layer attendance verification:**
  1. Time-bound 4-digit code (announced verbally in class)
  2. GPS proximity check (Haversine distance formula, student must be near teacher's location)
  3. AI face recognition (live selfie compared against registered profile photo)
- **Live attendance dashboard** — teachers see real-time submission status during active sessions
- **Manual review & correction** — teachers can override AI results with logged reasons before finalizing
- **Automated reporting** — PDF and CSV export (smart summary + complete reference formats)
- **Attendance analytics** — subject-wise and overall percentage tracking for students
- **Profile management** — students and teachers can update their details and photo anytime
- **Self-service password reset**

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL (cloud-hosted) |
| Face Recognition | Face++ API |
| Image Storage | Cloudinary |
| Frontend | HTML, CSS, JavaScript (vanilla) |
| PDF/CSV Generation | ReportLab, csv module |
| Authentication | Werkzeug password hashing, Flask sessions |
| Deployment | Render (Gunicorn WSGI server) |
| Version Control | Git, GitHub |

## Core Algorithms & Logic

- **Haversine Formula** — calculates real-world distance between two GPS coordinates on Earth's curved surface, used to verify a student is physically near the teacher when submitting attendance
- **Face similarity matching** — deep learning-based facial comparison via Face++ API, returning a confidence score used against a calibrated threshold (70%) to determine presence
- **Time-window session validation** — server-side timestamp comparison (not relying on database server time) to enforce a 5-minute attendance submission window

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it and install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with the following variables:
   ```
   DB_HOST=
   DB_PORT=
   DB_USER=
   DB_PASSWORD=
   DB_NAME=
   SECRET_KEY=
   CLOUDINARY_CLOUD_NAME=
   CLOUDINARY_API_KEY=
   CLOUDINARY_API_SECRET=
   FACEPP_API_KEY=
   FACEPP_API_SECRET=
   ```
5. Run the database schema setup (see `/schema` or run provided SQL statements)
6. Start the app: `python app.py`

## Known Limitations

- Face verification compares static image similarity; does not yet include liveness detection (blink/movement check) to prevent photo-spoofing — planned future enhancement
- Free-tier database has limited concurrent connection capacity
- Class/roster management (bulk student upload via Excel/CSV per class section) is planned for a future phase

## Future Roadmap

- Class-based roster system with Excel/CSV bulk upload and teacher-managed student lists
- Liveness detection to prevent static-photo spoofing
- Mobile app (React Native) conversion
- Admin-level college-wide analytics dashboard

## Author

Built as a solo full-stack project, covering backend development, database design, third-party API integration, and cloud deployment.
