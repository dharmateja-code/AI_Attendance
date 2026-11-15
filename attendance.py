"""
attendance.py - Attendance Records Viewing, Filtering, Manual Marking & Direct Exports.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import db
from reports import report_engine, REPORTS_DIR


class AttendanceRecordsFrame(tk.Frame):
    """Attendance log explorer and management view."""

    def __init__(self, parent, on_back_callback=None):
        super().__init__(parent, bg="#F8FAFC")
        self.parent = parent
        self.on_back_callback = on_back_callback

        self.setup_ui()
        self.load_attendance_data()

    def setup_ui(self):
        # Header Bar
        header = tk.Frame(self, bg="#1E293B", height=60)
        header.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            header,
            text="Attendance Logs & Attendance Analytics",
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

        # Main Body
        body = tk.Frame(self, bg="#F8FAFC")
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Filter & Action Control Card
        control_card = tk.LabelFrame(
            body,
            text=" Filter & Quick Actions ",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            relief=tk.GROOVE,
            bd=1
        )
        control_card.pack(fill=tk.X, pady=(0, 10), ipady=8, ipadx=10)

        # Filters Row
        f_row = tk.Frame(control_card, bg="#FFFFFF")
        f_row.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(f_row, text="Date (YYYY-MM-DD):", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(side=tk.LEFT, padx=(0, 5))
        self.ent_date = ttk.Entry(f_row, width=14)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.pack(side=tk.LEFT, padx=(0, 10))

        btn_filter_today = tk.Button(f_row, text="Filter Date", bg="#4F46E5", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.filter_by_date)
        btn_filter_today.pack(side=tk.LEFT, padx=3)

        btn_show_all = tk.Button(f_row, text="Show All Dates", bg="#64748B", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.load_attendance_data)
        btn_show_all.pack(side=tk.LEFT, padx=3)

        # Search box
        tk.Label(f_row, text="Search Roll / Name:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(side=tk.LEFT, padx=(20, 5))
        self.ent_search = ttk.Entry(f_row, width=16)
        self.ent_search.pack(side=tk.LEFT, padx=(0, 5))

        btn_search = tk.Button(f_row, text="Search", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.search_logs)
        btn_search.pack(side=tk.LEFT, padx=3)

        # Manual Entry Button
        btn_manual = tk.Button(f_row, text="+ Manual Entry", bg="#10B981", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.open_manual_entry_dialog)
        btn_manual.pack(side=tk.RIGHT, padx=5)

        # Export Actions Row
        exp_row = tk.Frame(control_card, bg="#FFFFFF")
        exp_row.pack(fill=tk.X, padx=10, pady=(6, 0))

        btn_exp_daily_excel = tk.Button(exp_row, text="Export Daily (Excel .xlsx)", bg="#059669", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=lambda: self.export_report("daily_excel"))
        btn_exp_daily_excel.pack(side=tk.LEFT, padx=3)

        btn_exp_daily_csv = tk.Button(exp_row, text="Export Daily (CSV)", bg="#10B981", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=lambda: self.export_report("daily_csv"))
        btn_exp_daily_csv.pack(side=tk.LEFT, padx=3)

        btn_exp_summary = tk.Button(exp_row, text="Export Semester Summary (75% Check)", bg="#7C3AED", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=lambda: self.export_report("summary_excel"))
        btn_exp_summary.pack(side=tk.LEFT, padx=3)

        btn_open_folder = tk.Button(exp_row, text="📂 Open Reports Folder", bg="#475569", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.open_reports_folder)
        btn_open_folder.pack(side=tk.RIGHT, padx=3)

        # Table Container
        table_card = tk.Frame(body, bg="#FFFFFF", bd=1, relief=tk.GROOVE)
        table_card.pack(fill=tk.BOTH, expand=True)

        columns = ("Rec ID", "Student ID", "Roll No", "Student Name", "Department", "Date", "Check-in Time", "Status", "Confidence")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=18)

        self.tree.heading("Rec ID", text="Rec ID")
        self.tree.heading("Student ID", text="ID")
        self.tree.heading("Roll No", text="Roll No")
        self.tree.heading("Student Name", text="Student Name")
        self.tree.heading("Department", text="Department")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Check-in Time", text="Check-in Time")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Confidence", text="Confidence")

        self.tree.column("Rec ID", width=55, anchor="center")
        self.tree.column("Student ID", width=50, anchor="center")
        self.tree.column("Roll No", width=85, anchor="center")
        self.tree.column("Student Name", width=140, anchor="w")
        self.tree.column("Department", width=110, anchor="w")
        self.tree.column("Date", width=85, anchor="center")
        self.tree.column("Check-in Time", width=85, anchor="center")
        self.tree.column("Status", width=80, anchor="center")
        self.tree.column("Confidence", width=80, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=tree_scroll_y.set)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_attendance_data(self, date_filter=None, search_keyword=None):
        """Fetches and renders attendance records."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        records = db.get_attendance_records(date_filter=date_filter)

        for r in records:
            if search_keyword:
                kw = search_keyword.lower()
                if (kw not in str(r['student_id']).lower() and 
                    kw not in r['roll_no'].lower() and 
                    kw not in r['name'].lower()):
                    continue

            conf_str = f"{int(r.get('confidence_score') or 0)}%"
            self.tree.insert("", tk.END, values=(
                r['attendance_id'],
                r['student_id'],
                r['roll_no'],
                r['name'],
                r['department'],
                r['date'],
                r['time'],
                r['status'],
                conf_str
            ))

    def filter_by_date(self):
        d = self.ent_date.get().strip()
        self.load_attendance_data(date_filter=d)

    def search_logs(self):
        kw = self.ent_search.get().strip()
        d = self.ent_date.get().strip() if self.ent_date.get().strip() else None
        self.load_attendance_data(date_filter=d, search_keyword=kw)

    def open_manual_entry_dialog(self):
        """Allows manual attendance marking in case of facial recognition override."""
        top = tk.Toplevel(self)
        top.title("Manual Attendance Entry")
        top.geometry("380x240")
        top.configure(bg="#0F172A")
        top.grab_set()

        tk.Label(top, text="Manual Attendance Override", font=("Segoe UI", 11, "bold"), fg="#38BDF8", bg="#0F172A").pack(pady=15)

        f = tk.Frame(top, bg="#0F172A")
        f.pack(pady=5)

        tk.Label(f, text="Student ID (Integer):", font=("Segoe UI", 9, "bold"), fg="#F8FAFC", bg="#0F172A").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        ent_mid = ttk.Entry(f, width=15)
        ent_mid.grid(row=0, column=1, padx=5, pady=8)

        def submit_manual():
            try:
                sid = int(ent_mid.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numeric Student ID.")
                return

            res, msg, student = db.record_attendance(sid, confidence=100.0)
            if res == "SUCCESS":
                messagebox.showinfo("Success", f"Attendance marked manually for {student['name']}.")
                top.destroy()
                self.load_attendance_data()
            elif res == "ALREADY_MARKED":
                messagebox.showwarning("Notice", msg)
            else:
                messagebox.showerror("Failed", msg)

        btn_sub = tk.Button(top, text="Mark Present", bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15, pady=6, command=submit_manual)
        btn_sub.pack(pady=15)

    def export_report(self, report_type):
        target_date = self.ent_date.get().strip() or None

        if report_type == "daily_excel":
            success, res = report_engine.export_daily_report(date_str=target_date, file_format="excel")
        elif report_type == "daily_csv":
            success, res = report_engine.export_daily_report(date_str=target_date, file_format="csv")
        elif report_type == "summary_excel":
            success, res = report_engine.export_cumulative_summary(file_format="excel")
        else:
            return

        if success:
            messagebox.showinfo("Report Exported", f"Report saved successfully!\nLocation:\n{res}")
        else:
            messagebox.showerror("Export Error", res)

    def open_reports_folder(self):
        try:
            os.startfile(REPORTS_DIR)
        except Exception:
            messagebox.showinfo("Reports Path", f"Reports are saved at:\n{REPORTS_DIR}")
