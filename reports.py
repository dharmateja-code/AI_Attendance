"""
reports.py - Attendance Reporting & Analytics Engine.
Generates CSV and styled Excel spreadsheets with attendance statistics and exam eligibility.
"""

import os
from datetime import datetime
import pandas as pd
from database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ReportGenerator:
    """Generates daily, monthly, and student-wise attendance reports in CSV/Excel."""

    def __init__(self):
        pass

    def export_daily_report(self, date_str=None, file_format="excel"):
        """
        Exports daily attendance for date_str (YYYY-MM-DD).
        Defaults to current date if omitted.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        records = db.get_attendance_records(date_filter=date_str)
        if not records:
            return False, f"No attendance records found for date: {date_str}"

        df = pd.DataFrame(records)
        columns_map = {
            'attendance_id': 'Record ID',
            'student_id': 'Student ID',
            'roll_no': 'Roll Number',
            'name': 'Student Name',
            'department': 'Department',
            'year': 'Year',
            'date': 'Date',
            'time': 'Check-In Time',
            'status': 'Attendance Status',
            'confidence_score': 'Match Confidence (%)'
        }
        df = df.rename(columns=columns_map)
        selected_cols = [c for c in columns_map.values() if c in df.columns]
        df = df[selected_cols]

        filename = f"Daily_Attendance_{date_str}.{'xlsx' if file_format == 'excel' else 'csv'}"
        filepath = os.path.join(REPORTS_DIR, filename)

        try:
            if file_format == "excel":
                self._write_styled_excel(df, filepath, sheet_name=f"Daily_{date_str}", title=f"Daily Attendance Report - {date_str}")
            else:
                df.to_csv(filepath, index=False)
            return True, filepath
        except Exception as e:
            return False, f"Failed to export daily report: {str(e)}"

    def export_monthly_report(self, year_month=None, file_format="excel"):
        """
        Exports attendance for a given month (YYYY-MM).
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        all_records = db.get_attendance_records()
        filtered = [r for r in all_records if str(r['date']).startswith(year_month)]

        if not filtered:
            return False, f"No attendance records found for month: {year_month}"

        df = pd.DataFrame(filtered)
        columns_map = {
            'attendance_id': 'Record ID',
            'student_id': 'Student ID',
            'roll_no': 'Roll Number',
            'name': 'Student Name',
            'department': 'Department',
            'year': 'Year',
            'date': 'Date',
            'time': 'Check-In Time',
            'status': 'Status'
        }
        df = df.rename(columns=columns_map)
        selected_cols = [c for c in columns_map.values() if c in df.columns]
        df = df[selected_cols]

        filename = f"Monthly_Attendance_{year_month}.{'xlsx' if file_format == 'excel' else 'csv'}"
        filepath = os.path.join(REPORTS_DIR, filename)

        try:
            if file_format == "excel":
                self._write_styled_excel(df, filepath, sheet_name=f"Month_{year_month}", title=f"Monthly Attendance Report - {year_month}")
            else:
                df.to_csv(filepath, index=False)
            return True, filepath
        except Exception as e:
            return False, f"Failed to export monthly report: {str(e)}"

    def export_cumulative_summary(self, file_format="excel"):
        """
        Generates overall student attendance percentage and exam eligibility (75% rule).
        """
        students = db.get_all_students()
        attendance = db.get_attendance_records()

        if not students:
            return False, "No students registered in the system."

        # Calculate unique active days in system
        unique_dates = set(r['date'] for r in attendance)
        total_working_days = max(1, len(unique_dates))

        summary_rows = []
        for s in students:
            s_id = s['student_id']
            # Count days attended
            days_attended = len([r for r in attendance if r['student_id'] == s_id])
            pct = round((days_attended / total_working_days) * 100, 2)
            eligibility = "Eligible" if pct >= 75.0 else "Shortage (< 75%)"

            summary_rows.append({
                'Student ID': s_id,
                'Roll Number': s['roll_no'],
                'Student Name': s['name'],
                'Department': s['department'],
                'Year': s['year'],
                'Total Working Days': total_working_days,
                'Days Present': days_attended,
                'Attendance %': f"{pct}%",
                'Exam Eligibility': eligibility
            })

        df = pd.DataFrame(summary_rows)
        filename = f"Student_Attendance_Summary_{datetime.now().strftime('%Y%m%d')}.{'xlsx' if file_format == 'excel' else 'csv'}"
        filepath = os.path.join(REPORTS_DIR, filename)

        try:
            if file_format == "excel":
                self._write_styled_excel(df, filepath, sheet_name="Attendance_Summary", title="Cumulative Student Attendance Summary")
            else:
                df.to_csv(filepath, index=False)
            return True, filepath
        except Exception as e:
            return False, f"Failed to export cumulative report: {str(e)}"

    def _write_styled_excel(self, df, filepath, sheet_name="Sheet1", title="Attendance Report"):
        """Writes DataFrame to styled Excel workbook with headers, styling, and column width formatting."""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Title banner at top
            worksheet.cell(row=1, column=1, value=title)
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            title_font = Font(name="Segoe UI", size=14, bold=True, color="1E293B")
            worksheet.cell(row=1, column=1).font = title_font

            # Header styles (Row 3)
            header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
            border_thin = Border(
                left=Side(style='thin', color='CBD5E1'),
                right=Side(style='thin', color='CBD5E1'),
                top=Side(style='thin', color='CBD5E1'),
                bottom=Side(style='thin', color='CBD5E1')
            )

            for col_num in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=3, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Format data cells
            for row in worksheet.iter_rows(min_row=4, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
                for cell in row:
                    cell.border = border_thin
                    cell.font = Font(name="Segoe UI", size=9)

            # Auto-fit column widths
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)


report_engine = ReportGenerator()
