"""
registration.py - Student Registration & Management GUI.
Allows adding, updating, deleting students, searching, and triggering facial sample capture.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import db
from face_capture import face_manager


class StudentRegistrationFrame(tk.Frame):
    """Student registration and CRUD interface."""

    def __init__(self, parent, on_back_callback=None):
        super().__init__(parent, bg="#F8FAFC")
        self.parent = parent
        self.on_back_callback = on_back_callback

        self.setup_ui()
        self.load_students()

    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg="#1E293B", height=60)
        header.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            header,
            text="Student Registration & Record Management",
            font=("Segoe UI", 13, "bold"),
            fg="#F8FAFC",
            bg="#1E293B"
        ).pack(side=tk.LEFT, padx=20, pady=15)

        if self.on_back_callback:
            btn_back = tk.Button(
                header,
                text="← Back to Dashboard",
                font=("Segoe UI", 9, "bold"),
                bg="#334155",
                fg="#F8FAFC",
                relief=tk.FLAT,
                padx=12,
                pady=5,
                command=self.on_back_callback
            )
            btn_back.pack(side=tk.RIGHT, padx=20)

        # Content Container (2 Columns: Left = Form, Right = Records Table)
        body = tk.Frame(self, bg="#F8FAFC")
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # ================= LEFT: REGISTRATION FORM =================
        form_card = tk.LabelFrame(
            body,
            text=" Student Information Form ",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            relief=tk.GROOVE,
            bd=1
        )
        form_card.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 15), pady=5, ipadx=10, ipady=10)

        fields = [
            ("Student ID (Integer):", "ent_id"),
            ("Roll Number:", "ent_roll"),
            ("Full Name:", "ent_name"),
            ("Department:", "cmb_dept"),
            ("Year:", "cmb_year"),
            ("Semester:", "cmb_sem"),
            ("Gender:", "cmb_gender"),
            ("Email Address:", "ent_email"),
            ("Phone Number:", "ent_phone"),
        ]

        self.entries = {}

        row_idx = 0
        for label_text, var_name in fields:
            tk.Label(
                form_card,
                text=label_text,
                font=("Segoe UI", 9, "bold"),
                fg="#334155",
                bg="#FFFFFF"
            ).grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)

            if var_name == "cmb_dept":
                widget = ttk.Combobox(
                    form_card,
                    values=["Computer Science (CSE)", "Information Tech (IT)", "Electronics (ECE)", "Electrical (EEE)", "Mechanical (ME)", "Civil (CE)"],
                    state="readonly",
                    width=26
                )
            elif var_name == "cmb_year":
                widget = ttk.Combobox(
                    form_card,
                    values=["First Year", "Second Year", "Third Year", "Final Year"],
                    state="readonly",
                    width=26
                )
            elif var_name == "cmb_sem":
                widget = ttk.Combobox(
                    form_card,
                    values=["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6", "Semester 7", "Semester 8"],
                    state="readonly",
                    width=26
                )
            elif var_name == "cmb_gender":
                widget = ttk.Combobox(
                    form_card,
                    values=["Male", "Female", "Other"],
                    state="readonly",
                    width=26
                )
            else:
                widget = ttk.Entry(form_card, width=28, font=("Segoe UI", 9))

            widget.grid(row=row_idx, column=1, padx=10, pady=5, sticky="w")
            self.entries[var_name] = widget
            row_idx += 1

        # CRUD Action Buttons Grid
        btn_frame = tk.Frame(form_card, bg="#FFFFFF")
        btn_frame.grid(row=row_idx, column=0, columnspan=2, pady=12)

        btn_add = tk.Button(
            btn_frame, text="Add Student", bg="#10B981", fg="white",
            font=("Segoe UI", 9, "bold"), width=12, relief=tk.FLAT, command=self.save_student
        )
        btn_add.grid(row=0, column=0, padx=4, pady=4)

        btn_update = tk.Button(
            btn_frame, text="Update", bg="#3B82F6", fg="white",
            font=("Segoe UI", 9, "bold"), width=10, relief=tk.FLAT, command=self.update_student
        )
        btn_update.grid(row=0, column=1, padx=4, pady=4)

        btn_delete = tk.Button(
            btn_frame, text="Delete", bg="#EF4444", fg="white",
            font=("Segoe UI", 9, "bold"), width=10, relief=tk.FLAT, command=self.delete_student
        )
        btn_delete.grid(row=0, column=2, padx=4, pady=4)

        btn_clear = tk.Button(
            btn_frame, text="Clear Form", bg="#64748B", fg="white",
            font=("Segoe UI", 9, "bold"), width=10, relief=tk.FLAT, command=self.clear_form
        )
        btn_clear.grid(row=0, column=3, padx=4, pady=4)

        # Facial Dataset Actions
        face_action_frame = tk.LabelFrame(
            form_card,
            text=" Facial Biometric Actions ",
            font=("Segoe UI", 9, "bold"),
            fg="#4F46E5",
            bg="#FFFFFF"
        )
        face_action_frame.grid(row=row_idx + 1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        btn_capture = tk.Button(
            face_action_frame,
            text="📷 Capture Face Samples (Webcam)",
            bg="#4F46E5",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            pady=6,
            command=self.launch_face_capture
        )
        btn_capture.pack(fill=tk.X, padx=10, pady=5)

        btn_train = tk.Button(
            face_action_frame,
            text="⚡ Train LBPH Model Manually",
            bg="#0284C7",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=5,
            command=self.manual_train_model
        )
        btn_train.pack(fill=tk.X, padx=10, pady=(0, 5))

        # ================= RIGHT: RECORDS TABLE & SEARCH =================
        table_card = tk.LabelFrame(
            body,
            text=" Registered Students Directory ",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            relief=tk.GROOVE,
            bd=1
        )
        table_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=5)

        # Search Bar
        search_frame = tk.Frame(table_card, bg="#FFFFFF")
        search_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(search_frame, text="Search by Roll No / Name:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(side=tk.LEFT)
        self.ent_search = ttk.Entry(search_frame, width=22)
        self.ent_search.pack(side=tk.LEFT, padx=8)

        btn_search = tk.Button(search_frame, text="Search", bg="#4F46E5", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.search_students)
        btn_search.pack(side=tk.LEFT, padx=3)

        btn_refresh = tk.Button(search_frame, text="Refresh All", bg="#64748B", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.load_students)
        btn_refresh.pack(side=tk.LEFT, padx=3)

        # Treeview
        columns = ("ID", "Roll", "Name", "Dept", "Year", "Gender", "Sample Status")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=16)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Roll", text="Roll No")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Dept", text="Department")
        self.tree.heading("Year", text="Year")
        self.tree.heading("Gender", text="Gender")
        self.tree.heading("Sample Status", text="Biometrics")

        self.tree.column("ID", width=45, anchor="center")
        self.tree.column("Roll", width=85, anchor="center")
        self.tree.column("Name", width=140, anchor="w")
        self.tree.column("Dept", width=110, anchor="w")
        self.tree.column("Year", width=85, anchor="center")
        self.tree.column("Gender", width=65, anchor="center")
        self.tree.column("Sample Status", width=95, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=tree_scroll_y.set)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

    def load_students(self, filter_query=None):
        """Populates Treeview with registered students."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        students = db.get_all_students()
        for s in students:
            if filter_query:
                q = filter_query.lower()
                if q not in str(s['student_id']).lower() and q not in s['roll_no'].lower() and q not in s['name'].lower():
                    continue

            self.tree.insert("", tk.END, values=(
                s['student_id'],
                s['roll_no'],
                s['name'],
                s['department'],
                s['year'],
                s.get('gender', '-'),
                s.get('photo_sample_status', 'Pending')
            ))

    def search_students(self):
        query = self.ent_search.get().strip()
        self.load_students(filter_query=query)

    def on_row_select(self, event):
        """Fills entry form with selected row details."""
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return

        student_id = values[0]
        student = db.get_student_by_id(int(student_id))
        if student:
            self.entries['ent_id'].delete(0, tk.END)
            self.entries['ent_id'].insert(0, student['student_id'])
            self.entries['ent_id'].config(state="readonly")

            self.entries['ent_roll'].delete(0, tk.END)
            self.entries['ent_roll'].insert(0, student['roll_no'])

            self.entries['ent_name'].delete(0, tk.END)
            self.entries['ent_name'].insert(0, student['name'])

            self.entries['cmb_dept'].set(student['department'])
            self.entries['cmb_year'].set(student['year'])
            self.entries['cmb_sem'].set(student.get('semester', ''))
            self.entries['cmb_gender'].set(student.get('gender', 'Male'))

            self.entries['ent_email'].delete(0, tk.END)
            self.entries['ent_email'].insert(0, student.get('email', ''))

            self.entries['ent_phone'].delete(0, tk.END)
            self.entries['ent_phone'].insert(0, student.get('phone', ''))

    def clear_form(self):
        """Resets all input fields."""
        self.entries['ent_id'].config(state="normal")
        for widget in self.entries.values():
            if isinstance(widget, ttk.Combobox):
                widget.set('')
            else:
                widget.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def save_student(self):
        """Validates and saves new student."""
        try:
            s_id = int(self.entries['ent_id'].get().strip())
        except ValueError:
            messagebox.showerror("Validation Error", "Student ID must be a positive integer (e.g., 101).")
            return

        roll = self.entries['ent_roll'].get().strip()
        name = self.entries['ent_name'].get().strip()
        dept = self.entries['cmb_dept'].get().strip()
        year = self.entries['cmb_year'].get().strip()
        sem = self.entries['cmb_sem'].get().strip()
        gender = self.entries['cmb_gender'].get().strip()
        email = self.entries['ent_email'].get().strip()
        phone = self.entries['ent_phone'].get().strip()

        if not (roll and name and dept and year):
            messagebox.showwarning("Incomplete Data", "Please fill in ID, Roll Number, Name, Department, and Year.")
            return

        success, msg = db.add_student(s_id, roll, name, dept, year, sem, gender, email, phone)
        if success:
            messagebox.showinfo("Success", msg)
            self.load_students()
            self.clear_form()
        else:
            messagebox.showerror("Error", msg)

    def update_student(self):
        """Updates selected student record."""
        try:
            s_id = int(self.entries['ent_id'].get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please select a student from the table first.")
            return

        roll = self.entries['ent_roll'].get().strip()
        name = self.entries['ent_name'].get().strip()
        dept = self.entries['cmb_dept'].get().strip()
        year = self.entries['cmb_year'].get().strip()
        sem = self.entries['cmb_sem'].get().strip()
        gender = self.entries['cmb_gender'].get().strip()
        email = self.entries['ent_email'].get().strip()
        phone = self.entries['ent_phone'].get().strip()

        success, msg = db.update_student(s_id, roll, name, dept, year, sem, gender, email, phone)
        if success:
            messagebox.showinfo("Success", msg)
            self.load_students()
            self.clear_form()
        else:
            messagebox.showerror("Error", msg)

    def delete_student(self):
        """Deletes selected student."""
        try:
            s_id = int(self.entries['ent_id'].get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please select a student to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Student ID {s_id}?\nAll attendance and face samples will be removed.")
        if confirm:
            success, msg = db.delete_student(s_id)
            if success:
                messagebox.showinfo("Deleted", msg)
                self.load_students()
                self.clear_form()
            else:
                messagebox.showerror("Error", msg)

    def launch_face_capture(self):
        """Opens the webcam capture modal for the selected student."""
        try:
            s_id = int(self.entries['ent_id'].get().strip())
            s_name = self.entries['ent_name'].get().strip()
        except ValueError:
            messagebox.showwarning("Selection Required", "Please select or add a student first to capture face samples.")
            return

        face_manager.open_capture_window(self, s_id, s_name, on_complete_callback=self.load_students)

    def manual_train_model(self):
        """Runs the LBPH training engine manually."""
        success, msg = face_manager.train_classifier()
        if success:
            messagebox.showinfo("Training Completed", msg)
            self.load_students()
        else:
            messagebox.showwarning("Training Notice", msg)
