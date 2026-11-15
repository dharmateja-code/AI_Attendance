"""
face_recognition.py - Real-time Face Recognition and Automatic Attendance Recording.
Integrates LBPH model, live webcam stream, duplicate prevention, and anti-spoofing heuristics.
"""

import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
from database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER_PATH = os.path.join(BASE_DIR, "classifier", "classifier.xml")


class FaceRecognitionWindow:
    """Live webcam recognition GUI with real-time feedback and attendance marking."""

    def __init__(self, parent):
        self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title("Live Face Recognition - Smart Attendance System")
        self.top.geometry("1100x700")
        self.top.configure(bg="#0F172A")
        self.top.grab_set()

        # Haar Cascades for Face and Eyes (check local assets folder first)
        local_face_cascade = os.path.join(BASE_DIR, "assets", "haarcascade_frontalface_default.xml")
        face_path = local_face_cascade if os.path.exists(local_face_cascade) else getattr(cv2.data, 'haarcascades', '') + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(face_path)

        local_eye_cascade = os.path.join(BASE_DIR, "assets", "haarcascade_eye.xml")
        eye_path = local_eye_cascade if os.path.exists(local_eye_cascade) else getattr(cv2.data, 'haarcascades', '') + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_path)

        # Load LBPH Classifier
        self.clf = None
        self.is_model_loaded = self.load_model()

        # Recognition tracking to avoid spamming database
        self.last_recognized_time = {}   # student_id -> timestamp
        self.recognized_log = []         # List of records marked in this session
        self.is_running = True
        self.anti_spoof_enabled = tk.BooleanVar(value=True)

        # Video capture
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

        # Build UI
        self.setup_ui()

        # Handle window close
        self.top.protocol("WM_DELETE_WINDOW", self.on_close)

        if self.is_model_loaded and self.cap.isOpened():
            self.top.after(100, self.update_frame)
        elif not self.is_model_loaded:
            messagebox.showwarning(
                "Model Not Found",
                "Trained classifier (classifier.xml) not found.\nPlease register students and capture face samples first!"
            )

    def load_model(self):
        """Loads trained LBPH model from disk."""
        if not os.path.exists(CLASSIFIER_PATH):
            return False
        try:
            if hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
                self.clf = cv2.face.LBPHFaceRecognizer_create()
                self.clf.read(CLASSIFIER_PATH)
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Failed to load classifier: {e}")
            return False

    def setup_ui(self):
        # Header Bar
        header = tk.Frame(self.top, bg="#1E293B", height=65)
        header.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            header,
            text="Real-Time Face Recognition & Automated Attendance",
            font=("Segoe UI", 14, "bold"),
            fg="#F8FAFC",
            bg="#1E293B"
        ).pack(side=tk.LEFT, padx=25, pady=15)

        chk_spoof = tk.Checkbutton(
            header,
            text="Enable Anti-Spoof Texture Check",
            variable=self.anti_spoof_enabled,
            font=("Segoe UI", 9),
            bg="#1E293B",
            fg="#38BDF8",
            selectcolor="#0F172A",
            activebackground="#1E293B"
        )
        chk_spoof.pack(side=tk.RIGHT, padx=25)

        # Main Layout Split (Left: Camera feed, Right: Live Attendance Log)
        main_body = tk.Frame(self.top, bg="#0F172A")
        main_body.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Left Container: Camera
        left_box = tk.Frame(main_body, bg="#1E293B", bd=1, relief=tk.SOLID)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        lbl_cam_title = tk.Label(
            left_box,
            text="LIVE CAMERA STREAM",
            font=("Segoe UI", 10, "bold"),
            fg="#94A3B8",
            bg="#1E293B"
        )
        lbl_cam_title.pack(anchor="w", padx=15, pady=8)

        self.canvas = tk.Label(left_box, bg="#000000", width=620, height=450)
        self.canvas.pack(padx=10, pady=5)

        # Notification Banner under camera
        self.lbl_alert = tk.Label(
            left_box,
            text="System Ready. Align your face with the camera frame.",
            font=("Segoe UI", 10, "bold"),
            fg="#38BDF8",
            bg="#1E293B",
            wraplength=600
        )
        self.lbl_alert.pack(pady=10)

        # Right Container: Attendance marked in this session
        right_box = tk.Frame(main_body, bg="#1E293B", width=420, bd=1, relief=tk.SOLID)
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        tk.Label(
            right_box,
            text="LIVE ATTENDANCE FEED",
            font=("Segoe UI", 10, "bold"),
            fg="#10B981",
            bg="#1E293B"
        ).pack(anchor="w", padx=15, pady=8)

        # Treeview for live attendance
        columns = ("ID", "Name", "Roll No", "Time", "Status")
        self.tree = ttk.Treeview(right_box, columns=columns, show="headings", height=18)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Roll No", text="Roll No")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Status", text="Status")

        self.tree.column("ID", width=45, anchor="center")
        self.tree.column("Name", width=120, anchor="w")
        self.tree.column("Roll No", width=80, anchor="center")
        self.tree.column("Time", width=65, anchor="center")
        self.tree.column("Status", width=85, anchor="center")

        scrollbar = ttk.Scrollbar(right_box, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Close Button
        btn_close = tk.Button(
            self.top,
            text="Close Scanner & Return to Dashboard",
            font=("Segoe UI", 10, "bold"),
            bg="#334155",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.on_close
        )
        btn_close.pack(pady=10)

    def check_anti_spoofing(self, gray_face):
        """
        Heuristic anti-spoofing check:
        1. Laplacian variance to detect blur / low-frequency flat phone screen images.
        2. Eye detection inside the facial region.
        """
        # Calculate Laplacian variance (texture / focus metric)
        laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        # High-definition printed paper or screens often have anomalous variance or lack depth
        is_texture_valid = laplacian_var > 40.0

        # Check for eye presence
        eyes = self.eye_cascade.detectMultiScale(gray_face, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
        has_eyes = len(eyes) >= 1

        return is_texture_valid and has_eyes, laplacian_var

    def update_frame(self):
        if not self.is_running:
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.lbl_alert.config(text="Camera disconnected or unavailable.", fg="#EF4444")
            self.top.after(100, self.update_frame)
            return

        frame = cv2.flip(frame, 1)  # Mirror view
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))

        display_frame = frame.copy()
        current_epoch = datetime.now().timestamp()

        for (x, y, w, h) in faces:
            face_roi_gray = gray[y:y + h, x:x + w]
            face_resized = cv2.resize(face_roi_gray, (200, 200))

            # Anti-spoofing filter
            is_live = True
            if self.anti_spoof_enabled.get():
                is_live, texture_val = self.check_anti_spoofing(face_roi_gray)
                if not is_live:
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 140, 255), 2)
                    cv2.putText(display_frame, "Warning: Spoof / Screen Suspected", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
                    continue

            # LBPH Prediction
            # predict() returns (id, distance). Lower distance = higher confidence.
            student_id, distance = self.clf.predict(face_resized)

            # Confidence mapping (distance ~0 is 100%, distance ~100 is 0%)
            confidence_pct = max(0, min(100, int(100 - (distance * 0.7))))

            # Threshold check: typically distance < 65 indicates positive match
            if distance < 68 and confidence_pct >= 50:
                student = db.get_student_by_id(student_id)
                if student:
                    student_name = student['name']
                    roll_no = student['roll_no']

                    # Draw Green Box
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (16, 185, 129), 2)
                    cv2.rectangle(display_frame, (x, y - 40), (x + w, y), (16, 185, 129), cv2.FILLED)
                    label = f"{student_name} ({confidence_pct}%)"
                    cv2.putText(display_frame, label, (x + 5, y - 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

                    # Mark attendance with cooldown of 5 seconds per student
                    last_time = self.last_recognized_time.get(student_id, 0)
                    if (current_epoch - last_time) > 5.0:
                        self.last_recognized_time[student_id] = current_epoch
                        res_status, message, _ = db.record_attendance(student_id, confidence_pct)

                        curr_time_str = datetime.now().strftime("%H:%M:%S")
                        if res_status == "SUCCESS":
                            self.lbl_alert.config(
                                text=f"SUCCESS: Attendance marked for {student_name} ({roll_no}) at {curr_time_str}",
                                fg="#10B981"
                            )
                            self.tree.insert("", 0, values=(student_id, student_name, roll_no, curr_time_str, "Marked"))
                        elif res_status == "ALREADY_MARKED":
                            self.lbl_alert.config(
                                text=f"INFO: {student_name} has already marked attendance for today.",
                                fg="#F59E0B"
                            )
                        else:
                            self.lbl_alert.config(text=f"ERROR: {message}", fg="#EF4444")

                else:
                    # ID recognized by model but not in DB
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(display_frame, "Unknown ID", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                # Unregistered / Unknown face
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(display_frame, (x, y - 30), (x + w, y), (0, 0, 255), cv2.FILLED)
                cv2.putText(display_frame, "Unknown Person", (x + 5, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                self.lbl_alert.config(text="Unknown person detected. Please register in the system.", fg="#EF4444")

        # Convert frame for Tkinter Display
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((620, 440), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.imgtk = imgtk
        self.canvas.configure(image=imgtk)

        self.top.after(35, self.update_frame)

    def on_close(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.top.destroy()
