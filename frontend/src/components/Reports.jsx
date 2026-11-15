import React, { useState } from 'react';
import { 
  FileSpreadsheet, 
  Download, 
  Calendar, 
  Award, 
  CheckCircle2, 
  AlertTriangle,
  FileText
} from 'lucide-react';

export default function Reports() {
  const [dailyDate, setDailyDate] = useState(new Date().toISOString().split('T')[0]);
  const [monthlyMonth, setMonthlyMonth] = useState(new Date().toISOString().slice(0, 7));

  const handleDownload = (type, params = {}) => {
    let query = `type=${type}`;
    if (params.date) query += `&date=${encodeURIComponent(params.date)}`;
    if (params.month) query += `&month=${encodeURIComponent(params.month)}`;
    window.open(`/api/reports/export?${query}`, '_blank');
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      
      {/* Top Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Academic Attendance Reports & Analytics</h1>
        <p className="text-sm text-slate-400 mt-1">
          Export verified attendance records into formatted Excel spreadsheets (.xlsx) and CSV with exam eligibility flags.
        </p>
      </div>

      {/* 3 Major Report Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Card 1: Daily Attendance Report */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-4">
              <Calendar className="w-6 h-6" />
            </div>
            <h2 className="text-base font-bold text-white">Daily Attendance Sheet</h2>
            <p className="text-xs text-slate-400 mt-1 mb-5">
              Comprehensive list of all students present for a chosen date, including exact check-in timestamps and AI confidence scores.
            </p>

            <div className="space-y-3 mb-6">
              <label className="block text-xs font-semibold text-slate-400">
                Select Report Date:
              </label>
              <input
                type="date"
                value={dailyDate}
                onChange={(e) => setDailyDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <button
              onClick={() => handleDownload('daily_excel', { date: dailyDate })}
              className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Download Excel (.xlsx)
            </button>
            <button
              onClick={() => handleDownload('daily_csv', { date: dailyDate })}
              className="w-full py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition flex items-center justify-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Download Raw CSV
            </button>
          </div>
        </div>

        {/* Card 2: Monthly Attendance Report */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mb-4">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <h2 className="text-base font-bold text-white">Monthly Attendance Sheet</h2>
            <p className="text-xs text-slate-400 mt-1 mb-5">
              Aggregated monthly attendance records across all academic departments for monthly faculty and departmental review.
            </p>

            <div className="space-y-3 mb-6">
              <label className="block text-xs font-semibold text-slate-400">
                Select Year & Month:
              </label>
              <input
                type="month"
                value={monthlyMonth}
                onChange={(e) => setMonthlyMonth(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <button
              onClick={() => handleDownload('monthly_excel', { month: monthlyMonth })}
              className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Download Monthly Excel (.xlsx)
            </button>
          </div>
        </div>

        {/* Card 3: Semester Cumulative & 75% Eligibility */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center mb-4">
              <Award className="w-6 h-6" />
            </div>
            <h2 className="text-base font-bold text-white">Semester Summary (75% Check)</h2>
            <p className="text-xs text-slate-400 mt-1 mb-5">
              Computes cumulative attendance percentage per student and automatically flags exam eligibility based on the university 75% mandatory threshold rule.
            </p>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs mb-6">
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Attendance ≥ 75%: Eligible for Final Exams</span>
              </div>
              <div className="flex items-center gap-2 text-rose-400">
                <AlertTriangle className="w-4 h-4" />
                <span>Attendance &lt; 75%: Attendance Shortage / Defaulter</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => handleDownload('summary_excel')}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-purple-600/20"
          >
            <Download className="w-4 h-4" />
            Export Semester Eligibility Report (.xlsx)
          </button>
        </div>

      </div>

      {/* Report Features Information */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <h3 className="text-sm font-bold text-white mb-3">Report Formatting Specifications</h3>
        <ul className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-400">
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5"></span>
            <span><strong>Automated OpenPyXL Styling:</strong> Formatted navy headers, thin cell borders, and centered text alignments.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5"></span>
            <span><strong>Auto-Fit Column Widths:</strong> Excel columns automatically adjust to match maximum string lengths.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5"></span>
            <span><strong>Direct Browser Downloads:</strong> Streamed directly from Flask API as binary attachments.</span>
          </li>
        </ul>
      </div>

    </div>
  );
}
