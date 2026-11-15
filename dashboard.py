"""
dashboard.py - Main Administrative Dashboard for Smart Attendance System.
Visualizes KPIs, system readiness, and serves as primary navigation hub.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import db
from registration import StudentRegistrationFrame
from attendance import AttendanceRecordsFrame
from face_recognition import FaceRecognitionWindow
from face_capture import face_manager, CLASSIFIER_PATH


class MainDashboard(tk.Tk):
    """Central Application Window and Navigation Router."""

    def __init__(self, admin_user=None):
        super().__init__()
        self.admin_user = admin_user or {"username": "admin", "full_name": "System Administrator"}

        self.title("Smart Attendance Management System - Admin Dashboard")
        self.geometry("1180x750")
        self.minsize(1050, 680)
        self.configure(bg="#0F172A")

        # Container for swappable screens (Dashboard, Registration, Attendance)
        self.container = tk.Frame(self, bg="#0F172A")
        self.container.pack(fill=tk.BOTH, expand=True)

        # Build Main Dashboard View
        self.show_dashboard_view()

    def clear_container(self):
        """Clears all widgets from container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_dashboard_view(self):
        """Builds and displays the core dashboard KPI view."""
        self.clear_container()

        # ================= TOP HEADER BAR =================
        header = tk.Frame(self.container, bg="#1E293B", height=70)
        header.pack(fill=tk.X, side=tk.TOP)

        title_frame = tk.Frame(header, bg="#1E293B")
        title_frame.pack(side=tk.LEFT, padx=25, pady=12)

        tk.Label(
            title_frame,
            text="🎓 SMART ATTENDANCE MANAGEMENT SYSTEM",
            font=("Segoe UI", 14, "bold"),
            fg="#F8FAFC",
            bg="#1E293B"
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="CSE Major / Mini Project | Automated Facial Biometrics",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#1E293B"
        ).pack(anchor="w")

        # Admin info & Logout on right
        user_frame = tk.Frame(header, bg="#1E293B")
        user_frame.pack(side=tk.RIGHT, padx=25, pady=15)

        tk.Label(
            user_frame,
            text=f"👤 {self.admin_user.get('full_name', 'Admin')}",
            font=("Segoe UI", 9, "bold"),
            fg="#38BDF8",
            bg="#1E293B"
        ).pack(side=tk.LEFT, padx=10)

        btn_logout = tk.Button(
            user_frame,
            text="Logout",
            font=("Segoe UI", 8, "bold"),
            bg="#EF4444",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self.logout
        )
        btn_logout.pack(side=tk.LEFT)

        # ================= BODY SCROLL/FRAME =================
        body = tk.Frame(self.container, bg="#0F172A")
        body.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Fetch KPIs from Database
        stats = db.get_dashboard_summary()
        total_st = stats['total_students']
        present_today = stats['present_today']
        absent_today = stats['absent_today']
        rate_pct = f"{round((present_today / total_st * 100), 1)}%" if total_st > 0 else "0.0%"

        # ================= STATS CARDS ROW =================
        stats_frame = tk.Frame(body, bg="#0F172A")
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        cards_data = [
            ("TOTAL STUDENTS", str(total_st), "#3B82F6", "👥 Registered in System"),
            ("PRESENT TODAY", str(present_today), "#10B981", f"📅 Date: {stats['today_date']}"),
            ("ABSENT TODAY", str(absent_today), "#EF4444", "⚠️ Missing from Class"),
            ("TODAY'S TURNOUT", rate_pct, "#8B5CF6", "📈 Attendance Ratio"),
        ]

        for title, val, color, note in cards_data:
            c = tk.Frame(stats_frame, bg="#1E293B", bd=0, relief=tk.FLAT, padx=15, pady=12)
            c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

            # Left accent color strip
            strip = tk.Frame(c, bg=color, width=4)
            strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

            content = tk.Frame(c, bg="#1E293B")
            content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tk.Label(content, text=title, font=("Segoe UI", 8, "bold"), fg="#94A3B8", bg="#1E293B").pack(anchor="w")
            tk.Label(content, text=val, font=("Segoe UI", 20, "bold"), fg="#F8FAFC", bg="#1E293B").pack(anchor="w", pady=2)
            tk.Label(content, text=note, font=("Segoe UI", 8), fg="#64748B", bg="#1E293B").pack(anchor="w")

        # ================= ACTION HUB TILES =================
        actions_title = tk.Label(body, text="SYSTEM ACTIONS & MODULES", font=("Segoe UI", 11, "bold"), fg="#CBD5E1", bg="#0F172A")
        actions_title.pack(anchor="w", pady=(10, 8))

        tiles_frame = tk.Frame(body, bg="#0F172A")
        tiles_frame.pack(fill=tk.X, pady=(0, 20))

        # Tile 1: Live Recognition
        self._build_action_tile(
            tiles_frame,
            title="📷 LIVE RECOGNITION SCANNER",
            desc="Open webcam to scan student faces and automatically record attendance in real-time.",
            btn_text="Launch Scanner",
            btn_bg="#10B981",
            command=self.launch_scanner
        )

        # Tile 2: Student Registration
        self._build_action_tile(
            tiles_frame,
            title="📝 STUDENT REGISTRATION",
            desc="Register student profiles, view directories, capture face photos, and manage records.",
            btn_text="Manage Students",
            btn_bg="#4F46E5",
            command=self.show_registration_view
        )

        # Tile 3: Attendance Logs
        self._build_action_tile(
            tiles_frame,
            title="📊 ATTENDANCE RECORDS",
            desc="Inspect attendance tables, filter by specific dates, perform manual entries, and search.",
            btn_text="View Attendance",
            btn_bg="#0284C7",
            command=self.show_attendance_view
        )

        # ================= SYSTEM STATUS & QUICK ACTIONS =================
        bottom_frame = tk.Frame(body, bg="#1E293B", padx=20, pady=15)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            bottom_frame,
            text="SYSTEM READINESS & AI MODEL STATUS",
            font=("Segoe UI", 10, "bold"),
            fg="#38BDF8",
            bg="#1E293B"
        ).pack(anchor="w", pady=(0, 10))

        status_grid = tk.Frame(bottom_frame, bg="#1E293B")
        status_grid.pack(fill=tk.X)

        db_engine = "MySQL Server (Localhost:3306)" if db.use_mysql else "Local SQLite Engine (smart_attendance.db)"
        model_status = "✅ Model Ready (classifier.xml exists)" if os.path.exists(CLASSIFIER_PATH) else "⚠️ Model Not Trained Yet (Capture samples and train)"

        statuses = [
            ("Database Engine:", db_engine, "#10B981"),
            ("Face Recognition Algorithm:", "Local Binary Pattern Histograms (LBPH)", "#38BDF8"),
            ("Classifier Status:", model_status, "#10B981" if os.path.exists(CLASSIFIER_PATH) else "#F59E0B"),
            ("Anti-Spoofing Filter:", "Heuristic Laplacian Variance + Biometric Eyes Check", "#A7F3D0")
        ]

        for i, (lbl, val, col) in enumerate(statuses):
            tk.Label(status_grid, text=lbl, font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(status_grid, text=val, font=("Segoe UI", 9), fg=col, bg="#1E293B").grid(row=i, column=1, sticky="w", padx=15, pady=3)

        btn_train_now = tk.Button(
            bottom_frame,
            text="⚡ Retrain LBPH Face Model Now",
            font=("Segoe UI", 9, "bold"),
            bg="#7C3AED",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self.quick_train
        )
        btn_train_now.pack(side=tk.LEFT, pady=(15, 0))

    def _build_action_tile(self, parent, title, desc, btn_text, btn_bg, command):
        """Constructs an individual action card widget."""
        card = tk.Frame(parent, bg="#1E293B", padx=16, pady=16)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        tk.Label(card, text=title, font=("Segoe UI", 11, "bold"), fg="#F8FAFC", bg="#1E293B").pack(anchor="w")
        tk.Label(card, text=desc, font=("Segoe UI", 8), fg="#94A3B8", bg="#1E293B", wraplength=260, justify=tk.LEFT).pack(anchor="w", pady=(6, 12))

        btn = tk.Button(
            card,
            text=btn_text,
            font=("Segoe UI", 9, "bold"),
            bg=btn_bg,
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=command
        )
        btn.pack(anchor="w")

    def launch_scanner(self):
        """Launches the Face Recognition camera scanner."""
        if not os.path.exists(CLASSIFIER_PATH):
            messagebox.showwarning(
                "Training Required",
                "Classifier model not found!\nPlease go to 'Student Registration' -> 'Capture Face Samples' and train the model first."
            )
            return
        FaceRecognitionWindow(self)

    def show_registration_view(self):
        """Switches view to Student Registration."""
        self.clear_container()
        reg_frame = StudentRegistrationFrame(self.container, on_back_callback=self.show_dashboard_view)
        reg_frame.pack(fill=tk.BOTH, expand=True)

    def show_attendance_view(self):
        """Switches view to Attendance Logs."""
        self.clear_container()
        att_frame = AttendanceRecordsFrame(self.container, on_back_callback=self.show_dashboard_view)
        att_frame.pack(fill=tk.BOTH, expand=True)

    def quick_train(self):
        """Retrains the LBPH model immediately."""
        success, msg = face_manager.train_classifier()
        if success:
            messagebox.showinfo("Model Updated", msg)
            self.show_dashboard_view()
        else:
            messagebox.showwarning("Notice", msg)

    def logout(self):
        """Logs out and re-launches the login window."""
        confirm = messagebox.askyesno("Confirm Logout", "Are you sure you want to sign out?")
        if confirm:
            self.destroy()
            from login import LoginWindow
            app = LoginWindow()
            app.mainloop()
