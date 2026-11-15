"""
database.py - Database Layer for Smart Attendance Management System
Supports MySQL (default) with automatic fallback to SQLite for easy local testing.
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime

# Optional MySQL connector import
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    MySQLError = Exception

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "smart_attendance.db")
CONFIG_PATH = os.path.join(BASE_DIR, "db_config.json")

# Default Configuration for MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_attendance_db',
    'port': 3306
}

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as cf:
            loaded_cfg = json.load(cf)
            DB_CONFIG.update(loaded_cfg)
    except Exception as e:
        print(f"[WARNING] Could not read db_config.json: {e}")

# Environment variables override (for Cloud Platforms like Render, Railway, AWS)
DB_CONFIG['host'] = os.environ.get('MYSQL_HOST') or os.environ.get('DB_HOST') or DB_CONFIG['host']
DB_CONFIG['user'] = os.environ.get('MYSQL_USER') or os.environ.get('DB_USER') or DB_CONFIG['user']
DB_CONFIG['password'] = os.environ.get('MYSQL_PASSWORD') or os.environ.get('DB_PASSWORD') or DB_CONFIG['password']
DB_CONFIG['database'] = os.environ.get('MYSQL_DATABASE') or os.environ.get('DB_NAME') or DB_CONFIG['database']
try:
    DB_CONFIG['port'] = int(os.environ.get('MYSQL_PORT') or os.environ.get('DB_PORT') or DB_CONFIG['port'])
except (ValueError, TypeError):
    DB_CONFIG['port'] = 3306


def hash_password(password: str) -> str:
    """Return SHA-256 hash of plaintext password."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class DatabaseManager:
    """Handles all database operations for MySQL and SQLite."""

    def __init__(self):
        self.use_mysql = False
        self._test_and_select_backend()
        self.initialize_tables()

    def _test_and_select_backend(self):
        """Attempts connection to MySQL. Falls back to SQLite if unreachable."""
        # On cloud instances without an external MySQL host configured, use SQLite directly
        is_cloud = bool(os.environ.get('RENDER') or os.environ.get('DYNO'))
        if is_cloud and DB_CONFIG['host'] == 'localhost':
            self.use_mysql = False
            os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
            print("[INFO] Cloud environment detected (Render). Using embedded database engine (smart_attendance.db).")
            return

        if MYSQL_AVAILABLE:
            try:
                # Test connection to MySQL server
                conn = mysql.connector.connect(
                    host=DB_CONFIG['host'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    port=DB_CONFIG['port']
                )
                if conn.is_connected():
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
                    cursor.close()
                    conn.close()
                    self.use_mysql = True
                    print("[INFO] Connected successfully to MySQL Database Server.")
                    return
            except Exception as e:
                print(f"[WARNING] MySQL connection failed: {e}")
                if "Access denied" in str(e):
                    print("  -> [HINT] If your MySQL 'root' user requires a password, set it in 'db_config.json'.")
                print("  -> Switching to local SQLite engine (smart_attendance.db).")

        self.use_mysql = False
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        print(f"[INFO] Using SQLite local database at: {SQLITE_DB_PATH}")

    def get_connection(self):
        """Returns active database connection and cursor."""
        if self.use_mysql:
            conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                port=DB_CONFIG['port']
            )
            return conn, conn.cursor(dictionary=True)
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn, conn.cursor()

    def initialize_tables(self):
        """Creates the required tables if they do not exist."""
        conn, cursor = self.get_connection()
        try:
            if self.use_mysql:
                # Admin
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        password_hash VARCHAR(128) NOT NULL,
                        full_name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB;
                """)
                # Students
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        student_id INT PRIMARY KEY,
                        roll_no VARCHAR(50) NOT NULL UNIQUE,
                        name VARCHAR(100) NOT NULL,
                        department VARCHAR(50) NOT NULL,
                        year VARCHAR(20) NOT NULL,
                        semester VARCHAR(20),
                        gender VARCHAR(15),
                        email VARCHAR(100),
                        phone VARCHAR(20),
                        photo_sample_status VARCHAR(20) DEFAULT 'Pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB;
                """)
                # Face Data
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS face_data (
                        face_id INT AUTO_INCREMENT PRIMARY KEY,
                        student_id INT NOT NULL,
                        image_path VARCHAR(255) NOT NULL,
                        sample_number INT NOT NULL,
                        captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
                    ) ENGINE=InnoDB;
                """)
                # Attendance with Unique (student_id, date) constraint
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attendance (
                        attendance_id INT AUTO_INCREMENT PRIMARY KEY,
                        student_id INT NOT NULL,
                        date DATE NOT NULL,
                        time TIME NOT NULL,
                        status VARCHAR(20) DEFAULT 'Present',
                        confidence_score FLOAT DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                        UNIQUE KEY unique_daily_attendance (student_id, date)
                    ) ENGINE=InnoDB;
                """)
                # Seed default admin if missing
                admin_pass_hash = hash_password("admin123")
                cursor.execute("""
                    INSERT IGNORE INTO admin (username, password_hash, full_name, email)
                    VALUES (%s, %s, %s, %s)
                """, ("admin", admin_pass_hash, "Project Administrator", "admin@college.edu"))

            else:
                # SQLite syntax
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        student_id INTEGER PRIMARY KEY,
                        roll_no TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        department TEXT NOT NULL,
                        year TEXT NOT NULL,
                        semester TEXT,
                        gender TEXT,
                        email TEXT,
                        phone TEXT,
                        photo_sample_status TEXT DEFAULT 'Pending',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS face_data (
                        face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        image_path TEXT NOT NULL,
                        sample_number INTEGER NOT NULL,
                        captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attendance (
                        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        status TEXT DEFAULT 'Present',
                        confidence_score REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                        UNIQUE(student_id, date)
                    );
                """)
                admin_pass_hash = hash_password("admin123")
                cursor.execute("""
                    INSERT OR IGNORE INTO admin (username, password_hash, full_name, email)
                    VALUES (?, ?, ?, ?)
                """, ("admin", admin_pass_hash, "Project Administrator", "admin@college.edu"))

            conn.commit()
        except Exception as e:
            print(f"[ERROR] Failed to initialize database tables: {e}")
        finally:
            cursor.close()
            conn.close()

    def verify_admin(self, username, password):
        """Verifies admin credentials."""
        conn, cursor = self.get_connection()
        p_hash = hash_password(password)
        try:
            if self.use_mysql:
                cursor.execute("SELECT * FROM admin WHERE username = %s AND password_hash = %s", (username, p_hash))
            else:
                cursor.execute("SELECT * FROM admin WHERE username = ? AND password_hash = ?", (username, p_hash))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
            conn.close()

    def add_student(self, student_id, roll_no, name, dept, year, sem, gender, email, phone):
        """Adds a new student record."""
        conn, cursor = self.get_connection()
        try:
            if self.use_mysql:
                query = """
                    INSERT INTO students (student_id, roll_no, name, department, year, semester, gender, email, phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (student_id, roll_no, name, dept, year, sem, gender, email, phone))
            else:
                query = """
                    INSERT INTO students (student_id, roll_no, name, department, year, semester, gender, email, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (student_id, roll_no, name, dept, year, sem, gender, email, phone))
            conn.commit()
            return True, "Student registered successfully!"
        except Exception as e:
            return False, f"Failed to register student: {str(e)}"
        finally:
            cursor.close()
            conn.close()

    def update_student(self, student_id, roll_no, name, dept, year, sem, gender, email, phone):
        """Updates an existing student record."""
        conn, cursor = self.get_connection()
        try:
            if self.use_mysql:
                query = """
                    UPDATE students 
                    SET roll_no=%s, name=%s, department=%s, year=%s, semester=%s, gender=%s, email=%s, phone=%s
                    WHERE student_id=%s
                """
                cursor.execute(query, (roll_no, name, dept, year, sem, gender, email, phone, student_id))
            else:
                query = """
                    UPDATE students 
                    SET roll_no=?, name=?, department=?, year=?, semester=?, gender=?, email=?, phone=?
                    WHERE student_id=?
                """
                cursor.execute(query, (roll_no, name, dept, year, sem, gender, email, phone, student_id))
            conn.commit()
            return True, "Student updated successfully!"
        except Exception as e:
            return False, f"Update failed: {str(e)}"
        finally:
            cursor.close()
            conn.close()

    def delete_student(self, student_id):
        """Deletes student record along with cascade face and attendance records."""
        conn, cursor = self.get_connection()
        try:
            if self.use_mysql:
                cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
            else:
                cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
            conn.commit()
            return True, "Student deleted successfully!"
        except Exception as e:
            return False, f"Deletion failed: {str(e)}"
        finally:
            cursor.close()
            conn.close()

    def get_all_students(self):
        """Retrieves list of all students."""
        conn, cursor = self.get_connection()
        try:
            cursor.execute("SELECT * FROM students ORDER BY student_id ASC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            cursor.close()
            conn.close()

    def get_student_by_id(self, student_id):
        """Finds student by their primary student_id."""
        conn, cursor = self.get_connection()
        try:
            if self.use_mysql:
                cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
            else:
                cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
            conn.close()

    def update_photo_sample_status(self, student_id, status="Sample Ready"):
        """Updates sample status for student."""
        conn, cursor = self.get_connection()
        try:
            if self.use_mysql:
                cursor.execute("UPDATE students SET photo_sample_status=%s WHERE student_id=%s", (status, student_id))
            else:
                cursor.execute("UPDATE students SET photo_sample_status=? WHERE student_id=?", (status, student_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def record_attendance(self, student_id, confidence=0.0):
        """
        Records attendance for student for the current date.
        Enforces duplicate prevention: if already marked today, returns ('EXISTS', info).
        """
        conn, cursor = self.get_connection()
        today_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        try:
            # 1. Fetch student info
            if self.use_mysql:
                cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
            else:
                cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
            student = cursor.fetchone()
            if not student:
                return "NOT_FOUND", "Student ID does not exist in database.", None

            student = dict(student)

            # 2. Check duplicate attendance for today
            if self.use_mysql:
                cursor.execute("SELECT * FROM attendance WHERE student_id=%s AND date=%s", (student_id, today_date))
            else:
                cursor.execute("SELECT * FROM attendance WHERE student_id=? AND date=?", (student_id, today_date))
            existing = cursor.fetchone()

            if existing:
                existing_dict = dict(existing)
                return "ALREADY_MARKED", f"Attendance already marked for today at {existing_dict.get('time')}", student

            # 3. Insert new attendance record
            if self.use_mysql:
                cursor.execute("""
                    INSERT INTO attendance (student_id, date, time, status, confidence_score)
                    VALUES (%s, %s, %s, %s, %s)
                """, (student_id, today_date, current_time, "Present", confidence))
            else:
                cursor.execute("""
                    INSERT INTO attendance (student_id, date, time, status, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, today_date, current_time, "Present", confidence))

            conn.commit()
            return "SUCCESS", f"Attendance recorded successfully at {current_time}", student

        except Exception as e:
            return "ERROR", f"Database error: {str(e)}", None
        finally:
            cursor.close()
            conn.close()

    def get_attendance_records(self, date_filter=None):
        """Fetches joined attendance records with student details."""
        conn, cursor = self.get_connection()
        try:
            query = """
                SELECT 
                    a.attendance_id,
                    a.student_id,
                    s.roll_no,
                    s.name,
                    s.department,
                    s.year,
                    a.date,
                    a.time,
                    a.status,
                    a.confidence_score
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
            """
            params = []
            if date_filter:
                query += " WHERE a.date = %s" if self.use_mysql else " WHERE a.date = ?"
                params.append(date_filter)

            query += " ORDER BY a.date DESC, a.time DESC"

            cursor.execute(query, tuple(params) if params else ())
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            cursor.close()
            conn.close()

    def get_dashboard_summary(self):
        """Returns statistics for dashboard metrics."""
        conn, cursor = self.get_connection()
        today_date = datetime.now().strftime("%Y-%m-%d")
        try:
            # Total Students
            cursor.execute("SELECT COUNT(*) AS total FROM students")
            total_students = cursor.fetchone()
            total_count = total_students['total'] if isinstance(total_students, dict) else total_students[0]

            # Present Today
            if self.use_mysql:
                cursor.execute("SELECT COUNT(DISTINCT student_id) AS present FROM attendance WHERE date=%s", (today_date,))
            else:
                cursor.execute("SELECT COUNT(DISTINCT student_id) AS present FROM attendance WHERE date=?", (today_date,))
            present_res = cursor.fetchone()
            present_count = present_res['present'] if isinstance(present_res, dict) else present_res[0]

            absent_count = max(0, total_count - present_count)

            # Department breakdown
            cursor.execute("SELECT department, COUNT(*) AS count FROM students GROUP BY department")
            dept_breakdown = [dict(r) for r in cursor.fetchall()]

            return {
                "total_students": total_count,
                "present_today": present_count,
                "absent_today": absent_count,
                "departments": dept_breakdown,
                "today_date": today_date
            }
        finally:
            cursor.close()
            conn.close()


# Global Singleton Database Instance
db = DatabaseManager()
