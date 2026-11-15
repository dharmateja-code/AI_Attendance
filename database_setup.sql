-- Smart Attendance Management System Using Face Recognition
-- MySQL Database Creation Script
-- Recommended for MySQL 8.0+ or XAMPP / WAMP MariaDB

CREATE DATABASE IF NOT EXISTS smart_attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_attendance_db;

-- 1. Admin Table
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Default Admin Credential (username: admin, password: admin123 hashed using SHA-256)
-- SHA-256 for 'admin123' is 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa82280f1a823e618
INSERT INTO admin (username, password_hash, full_name, email)
SELECT 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa82280f1a823e618', 'System Administrator', 'admin@college.edu'
WHERE NOT EXISTS (SELECT 1 FROM admin WHERE username = 'admin');

-- 2. Students Table
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

-- 3. Face Data Table
CREATE TABLE IF NOT EXISTS face_data (
    face_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    sample_number INT NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Attendance Table
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

-- Sample Seed Data for Testing
INSERT IGNORE INTO students (student_id, roll_no, name, department, year, semester, gender, email, phone, photo_sample_status)
VALUES 
(101, 'CSE21001', 'Aarav Sharma', 'CSE', 'Final Year', 'Semester 7', 'Male', 'aarav@college.edu', '9876543210', 'Sample Ready'),
(102, 'CSE21002', 'Priya Patel', 'CSE', 'Final Year', 'Semester 7', 'Female', 'priya@college.edu', '9876543211', 'Sample Ready'),
(103, 'ECE21005', 'Rohan Verma', 'ECE', 'Third Year', 'Semester 5', 'Male', 'rohan@college.edu', '9876543212', 'Pending');
