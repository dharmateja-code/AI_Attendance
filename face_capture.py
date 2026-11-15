"""
face_capture.py - Captures facial dataset samples using webcam and trains LBPH model.
"""

import os
import cv2
import numpy as np
from PIL import Image

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from PIL import ImageTk
    TK_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    tk = None
    ttk = None
    messagebox = None
    ImageTk = None
    TK_AVAILABLE = False

from database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
CLASSIFIER_DIR = os.path.join(BASE_DIR, "classifier")
CLASSIFIER_PATH = os.path.join(CLASSIFIER_DIR, "classifier.xml")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(CLASSIFIER_DIR, exist_ok=True)


class FaceCaptureManager:
    """Handles face sample capture and LBPH training."""

    def __init__(self):
        # Load Haar Cascade frontal face classifier (check local assets first)
        local_cascade = os.path.join(BASE_DIR, "assets", "haarcascade_frontalface_default.xml")
        if os.path.exists(local_cascade):
            cascade_path = local_cascade
        else:
            cascade_path = getattr(cv2.data, 'haarcascades', '') + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            print(f"[ERROR] Failed to load frontal face Haar Cascade from: {cascade_path}")

    def open_capture_window(self, parent, student_id, student_name, on_complete_callback=None):
        """Launches real-time camera capture dialog inside Tkinter."""
        if not TK_AVAILABLE:
            print("[WARNING] Tkinter is not available in this environment.")
            return
        cap_win = tk.Toplevel(parent)
        cap_win.title(f"Face Sample Collector - ID: {student_id} ({student_name})")
        cap_win.geometry("780x680")
        cap_win.configure(bg="#0F172A")
        cap_win.grab_set()  # Make modal

        # Title Header
        header = tk.Frame(cap_win, bg="#1E293B", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(
            header,
            text=f"Capturing Face Data for: {student_name} (ID: {student_id})",
            font=("Segoe UI", 13, "bold"),
            fg="#F8FAFC",
            bg="#1E293B"
        ).pack(pady=12)

        # Video Canvas
        canvas_frame = tk.Frame(cap_win, bg="#0F172A", bd=2, relief=tk.SOLID)
        canvas_frame.pack(pady=10)
        canvas = tk.Label(canvas_frame, bg="#000000", width=640, height=440)
        canvas.pack()

        # Progress and status bar
        status_frame = tk.Frame(cap_win, bg="#0F172A")
        status_frame.pack(fill=tk.X, padx=40, pady=5)

        progress_var = tk.IntVar(value=0)
        progress_bar = ttk.Progressbar(status_frame, variable=progress_var, maximum=60, length=700)
        progress_bar.pack(pady=5)

        lbl_status = tk.Label(
            status_frame,
            text="Initializing webcam... Please look directly into the camera.",
            font=("Segoe UI", 10),
            fg="#38BDF8",
            bg="#0F172A"
        )
        lbl_status.pack()

        # Capture Control State
        state = {
            "cap": None,
            "sample_count": 0,
            "max_samples": 60,
            "running": True
        }

        # Open Webcam
        state["cap"] = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not state["cap"].isOpened():
            # Fallback for standard video capture
            state["cap"] = cv2.VideoCapture(0)

        if not state["cap"].isOpened():
            messagebox.showerror("Camera Error", "Could not connect to webcam. Ensure no other application is using it.")
            cap_win.destroy()
            return

        def update_frame():
            if not state["running"]:
                return

            ret, frame = state["cap"].read()
            if not ret or frame is None:
                lbl_status.config(text="Camera read error. Retrying...", fg="#EF4444")
                cap_win.after(50, update_frame)
                return

            frame = cv2.flip(frame, 1)  # Mirror view
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(90, 90))

            display_frame = frame.copy()

            if len(faces) == 0:
                cv2.putText(display_frame, "No Face Detected - Look at camera", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif len(faces) > 1:
                cv2.putText(display_frame, "Multiple Faces Detected! Stay alone in frame", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            else:
                (x, y, w, h) = faces[0]
                # Draw green bounding box
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (16, 185, 129), 2)

                # Capture sample every 2-3 calls
                state["sample_count"] += 1
                sample_file = os.path.join(DATASET_DIR, f"user.{student_id}.{state['sample_count']}.jpg")
                face_crop = gray[y:y + h, x:x + w]
                face_resized = cv2.resize(face_crop, (200, 200))
                cv2.imwrite(sample_file, face_resized)

                progress_var.set(state["sample_count"])
                lbl_status.config(
                    text=f"Collecting samples: {state['sample_count']} / {state['max_samples']} | Move head slightly for varied angles",
                    fg="#10B981"
                )

                # Add sample overlay on video
                cv2.putText(display_frame, f"Sample: {state['sample_count']}/{state['max_samples']}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (16, 185, 129), 2)

            # Convert to Tkinter Image
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            img = img.resize((640, 420), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            canvas.imgtk = imgtk
            canvas.configure(image=imgtk)

            if state["sample_count"] >= state["max_samples"]:
                finish_capture()
                return

            cap_win.after(40, update_frame)

        def finish_capture():
            state["running"] = False
            if state["cap"] and state["cap"].isOpened():
                state["cap"].release()

            db.update_photo_sample_status(student_id, "Sample Ready")
            lbl_status.config(text="Sample collection complete! Training model...", fg="#10B981")

            # Trigger LBPH Training
            train_success, train_msg = self.train_classifier()

            if train_success:
                messagebox.showinfo(
                    "Success",
                    f"Successfully collected {state['max_samples']} face samples!\n\nModel trained automatically:\n{train_msg}"
                )
            else:
                messagebox.showwarning(
                    "Sample Saved",
                    f"Samples saved, but model training returned:\n{train_msg}"
                )

            cap_win.destroy()
            if on_complete_callback:
                on_complete_callback()

        def on_close():
            state["running"] = False
            if state["cap"] and state["cap"].isOpened():
                state["cap"].release()
            cap_win.destroy()

        cap_win.protocol("WM_DELETE_WINDOW", on_close)

        btn_cancel = tk.Button(
            cap_win,
            text="Cancel Capture",
            font=("Segoe UI", 10, "bold"),
            bg="#EF4444",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=on_close
        )
        btn_cancel.pack(pady=10)

        # Start capture loop
        cap_win.after(100, update_frame)

    def train_classifier(self):
        """
        Reads all images in dataset/, extracts student IDs,
        and trains an LBPH Face Recognizer, saving to classifier.xml.
        """
        image_paths = [os.path.join(DATASET_DIR, f) for f in os.listdir(DATASET_DIR) if f.endswith(".jpg")]

        if len(image_paths) == 0:
            return False, "No dataset images found in dataset folder. Please capture samples first."

        faces = []
        ids = []

        try:
            for img_path in image_paths:
                # Format: user.<student_id>.<sample_no>.jpg
                filename = os.path.basename(img_path)
                parts = filename.split(".")
                if len(parts) >= 3 and parts[0] == "user":
                    student_id = int(parts[1])
                    pil_img = Image.open(img_path).convert('L')  # Convert to grayscale
                    img_np = np.array(pil_img, 'uint8')

                    faces.append(img_np)
                    ids.append(student_id)

            if len(faces) == 0:
                return False, "No valid formatted user samples found to train."

            # Create LBPH recognizer
            if hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
                clf = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
            else:
                return False, "cv2.face module not found. Please ensure opencv-contrib-python is installed."

            clf.train(faces, np.array(ids))
            clf.write(CLASSIFIER_PATH)

            unique_students = len(set(ids))
            return True, f"Trained on {len(faces)} images across {unique_students} student(s).\nSaved to classifier.xml"

        except Exception as e:
            return False, f"Training failed with error: {str(e)}"


# Global Manager Instance
face_manager = FaceCaptureManager()
