"""
main.py - Entry Point for Smart Attendance Management System.
Configures runtime environment, initializes database, verifies OpenCV modules, and launches GUI.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox


def check_prerequisites():
    """Validates required folders and libraries."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subdirs = ["dataset", "classifier", "reports", "data", "assets"]
    for sd in subdirs:
        os.makedirs(os.path.join(base_dir, sd), exist_ok=True)

    try:
        import cv2
        print(f"[OK] OpenCV detected: Version {cv2.__version__}")
        if not hasattr(cv2, 'face'):
            print("[WARNING] cv2.face module missing! Ensure 'opencv-contrib-python' is installed.")
    except ImportError:
        print("[CRITICAL] OpenCV is not installed. Run: pip install opencv-contrib-python")

    try:
        import PIL
        print(f"[OK] Pillow detected: Version {PIL.__version__}")
    except ImportError:
        print("[CRITICAL] Pillow is not installed. Run: pip install pillow")


def configure_app_styles():
    """Sets modern visual styles for Tkinter ttk components."""
    style = ttk.Style()
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')

    # Treeview Styling
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground="#1E293B",
        rowheight=26,
        fieldbackground="#FFFFFF",
        font=("Segoe UI", 9)
    )
    style.configure(
        "Treeview.Heading",
        background="#1E293B",
        foreground="#FFFFFF",
        font=("Segoe UI", 9, "bold"),
        relief=tk.FLAT
    )
    style.map(
        "Treeview",
        background=[('selected', '#4F46E5')],
        foreground=[('selected', '#FFFFFF')]
    )

    # Progressbar
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor="#1E293B",
        bordercolor="#0F172A",
        background="#10B981",
        lightcolor="#10B981",
        darkcolor="#10B981"
    )


def main():
    print("=" * 65)
    print("  SMART ATTENDANCE MANAGEMENT SYSTEM USING FACE RECOGNITION")
    print("  College CSE Mini-Project | Python & OpenCV Biometrics")
    print("=" * 65)

    check_prerequisites()

    # Import and verify database layer
    try:
        from database import db
        print("[OK] Database layer initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Database initialization error: {e}")

    # Launch GUI
    from login import LoginWindow
    app = LoginWindow()
    configure_app_styles()
    app.mainloop()


if __name__ == "__main__":
    main()
