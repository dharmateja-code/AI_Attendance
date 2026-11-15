# Smart Attendance Management System Using Face Recognition

An automated, contactless biometric attendance management system powered by **Python**, **OpenCV (LBPH Algorithm)**, a **Flask REST API**, and a modern **React.js + Tailwind CSS** web dashboard (with an optional Tkinter desktop interface).

---

## 🌟 Key Features

- **Real-Time Facial Recognition:** High-speed webcam face detection and recognition using Haar Cascades and Local Binary Pattern Histograms (LBPH).
- **Anti-Spoofing Heuristics:** Laplacian texture variance and ocular verification to filter out static 2D photos and mobile screen spoofs.
- **Strict Duplicate Prevention:** Database-enforced `UNIQUE(student_id, date)` constraint and application-level cooldowns prevent multiple check-ins on the same day.
- **Modern React.js Dashboard:** Built with Vite, Tailwind CSS, and Lucide Icons, featuring live KPI cards, turnout percentages, and department breakdowns.
- **Live Recognition Video Stream:** Smooth 30 FPS MJPEG camera feed streamed directly into the browser with real-time recognition overlays and an auto-syncing attendance log feed.
- **Student Profile Management:** Register, update, and delete student records with a built-in webcam biometric dataset collector (60 frames) and one-click model training.
- **Automated Academic Reports:** Export formatted Daily and Monthly spreadsheets, as well as Semester Cumulative Summaries with mandatory university **75% Exam Eligibility** flags (`Eligible` vs. `Shortage`).
- **Dual-Engine Database Layer:** Connects to **MySQL 8.0+** with an automatic, zero-crash fallback to local **SQLite** (`smart_attendance.db`).

---

## 🛠️ Tech Stack

- **Computer Vision & AI:** Python 3, OpenCV (`opencv-contrib-python`), LBPH Algorithm, Haar Cascades
- **Backend & REST API:** Flask, Flask-CORS, Pillow, Pandas, OpenPyXL
- **Database:** MySQL (recommended) / SQLite (embedded fallback)
- **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide React
- **Alternative Desktop GUI:** Python Tkinter (included in `main.py`)

---

## 📁 Project Structure

```text
smart_attendance_system/
│
├── assets/                  # Haar Cascade classifiers (face & eye XMLs)
├── classifier/              # Trained LBPH model weights (classifier.xml)
├── data/                    # SQLite database storage (smart_attendance.db)
├── dataset/                 # Captured facial image samples (user.<id>.<sample>.jpg)
├── reports/                 # Generated Excel (.xlsx) and CSV attendance sheets
│
├── frontend/                # Modern React.js Web Application
│   ├── src/
│   │   ├── components/      # Dashboard, LiveScanner, StudentManagement, Reports, etc.
│   │   ├── App.jsx          # Main App shell & routing
│   │   └── index.css        # Tailwind styles & animations
│   ├── package.json
│   └── vite.config.js
│
├── database.py              # Centralized database manager (MySQL + SQLite)
├── database_setup.sql       # MySQL schema and initial seed data
├── db_config.example.json   # Template configuration for MySQL credentials
├── face_capture.py          # Webcam sample collector & LBPH trainer
├── face_recognition.py      # OpenCV recognition & anti-spoofing engine
├── reports.py               # Excel and CSV export generator
├── server.py                # Flask REST API & Video Streaming server
│
├── login.py                 # Tkinter Admin Login Window
├── dashboard.py             # Tkinter Desktop Dashboard
├── registration.py          # Tkinter Student Registration GUI
├── attendance.py            # Tkinter Attendance Records GUI
├── main.py                  # Tkinter Desktop Launcher
│
├── requirements.txt         # Python package dependencies
├── package.json             # Root npm script delegation
├── run_web_system.bat       # 1-Click launcher for Web Dashboard
└── README.md                # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12, 3.13, 3.14)
- Node.js 18+ and npm
- A laptop or external USB webcam

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/smart-attendance-system.git
cd smart-attendance-system

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
npm install --prefix frontend
```

### 3. Database Configuration (Optional)
The system automatically defaults to an embedded SQLite database if MySQL is not running. 

To use MySQL:
1. Run `database_setup.sql` in MySQL Workbench or phpMyAdmin (XAMPP).
2. Copy `db_config.example.json` to `db_config.json`:
   ```bash
   cp db_config.example.json db_config.json
   ```
3. Update your MySQL `password` and `port` in `db_config.json`.

---

## 🖥️ Running the Application

### Option A: Web Dashboard (React + Flask) — Recommended
Run the 1-click batch file on Windows:
```bash
.\run_web_system.bat
```
*Or run manually:*
```bash
python server.py
```
Open **`http://localhost:5000`** in your browser.

*(For frontend development with hot-reload, run `npm run dev` in another terminal and open `http://localhost:5173`).*

### Option B: Desktop Interface (Tkinter)
```bash
python main.py
```

---

## 🔑 Default Administrator Credentials

- **Username:** `admin`
- **Password:** `admin123`

---

## 📄 License
This project is open-source and developed for academic educational purposes (CSE Mini/Major Project).
