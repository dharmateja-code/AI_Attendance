"""
login.py - Administrator Authentication Screen.
Provides secure SHA-256 password validation and user credential management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import db
from dashboard import MainDashboard


class LoginWindow(tk.Tk):
    """Admin Login GUI."""

    def __init__(self):
        super().__init__()
        self.title("Smart Attendance System - Admin Portal")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(bg="#0F172A")

        # Center on screen
        self.eval('tk::PlaceWindow . center')

        self.setup_ui()

    def setup_ui(self):
        # Top Logo / Title Container
        top_frame = tk.Frame(self, bg="#0F172A")
        top_frame.pack(fill=tk.X, pady=(40, 20))

        tk.Label(
            top_frame,
            text="🎓",
            font=("Segoe UI", 36),
            bg="#0F172A",
            fg="#38BDF8"
        ).pack()

        tk.Label(
            top_frame,
            text="Smart Attendance Portal",
            font=("Segoe UI", 16, "bold"),
            fg="#F8FAFC",
            bg="#0F172A"
        ).pack(pady=(5, 2))

        tk.Label(
            top_frame,
            text="Face Recognition Biometric System",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#0F172A"
        ).pack()

        # Login Card
        card = tk.Frame(self, bg="#1E293B", padx=30, pady=25, bd=1, relief=tk.SOLID)
        card.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 40))

        tk.Label(
            card,
            text="Administrator Sign In",
            font=("Segoe UI", 11, "bold"),
            fg="#F8FAFC",
            bg="#1E293B"
        ).pack(anchor="w", pady=(0, 15))

        # Username Field
        tk.Label(
            card,
            text="Username",
            font=("Segoe UI", 9, "bold"),
            fg="#94A3B8",
            bg="#1E293B"
        ).pack(anchor="w", pady=(5, 2))

        self.ent_user = ttk.Entry(card, font=("Segoe UI", 10), width=32)
        self.ent_user.pack(fill=tk.X, pady=(0, 12), ipady=3)
        self.ent_user.insert(0, "admin")  # Default convenience

        # Password Field
        tk.Label(
            card,
            text="Password",
            font=("Segoe UI", 9, "bold"),
            fg="#94A3B8",
            bg="#1E293B"
        ).pack(anchor="w", pady=(5, 2))

        self.ent_pass = ttk.Entry(card, font=("Segoe UI", 10), show="•", width=32)
        self.ent_pass.pack(fill=tk.X, pady=(0, 5), ipady=3)
        self.ent_pass.insert(0, "admin123")  # Default convenience

        # Show password toggle
        self.show_pass_var = tk.BooleanVar(value=False)
        chk_show = tk.Checkbutton(
            card,
            text="Show Password",
            variable=self.show_pass_var,
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#1E293B",
            activebackground="#1E293B",
            selectcolor="#0F172A",
            command=self.toggle_password
        )
        chk_show.pack(anchor="w", pady=(0, 15))

        # Login Button
        btn_login = tk.Button(
            card,
            text="Sign In to Dashboard →",
            font=("Segoe UI", 10, "bold"),
            bg="#4F46E5",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self.handle_login
        )
        btn_login.pack(fill=tk.X, pady=(5, 12))

        # Helper credentials badge
        hint_frame = tk.Frame(card, bg="#0F172A", padx=10, pady=6)
        hint_frame.pack(fill=tk.X)
        tk.Label(
            hint_frame,
            text="Default Admin: admin | Password: admin123",
            font=("Segoe UI", 7),
            fg="#38BDF8",
            bg="#0F172A"
        ).pack()

        # Bind Enter key
        self.bind("<Return>", lambda event: self.handle_login())

    def toggle_password(self):
        if self.show_pass_var.get():
            self.ent_pass.config(show="")
        else:
            self.ent_pass.config(show="•")

    def handle_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Incomplete Fields", "Please enter both username and password.")
            return

        admin_record = db.verify_admin(username, password)
        if admin_record:
            self.destroy()
            app = MainDashboard(admin_user=admin_record)
            app.mainloop()
        else:
            messagebox.showerror("Access Denied", "Invalid admin credentials. Please try again.")


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
