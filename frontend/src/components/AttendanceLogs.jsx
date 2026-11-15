import React, { useState, useEffect } from 'react';
import { 
  ClipboardCheck, 
  Search, 
  Calendar, 
  Download, 
  UserCheck, 
  RefreshCw,
  FileSpreadsheet
} from 'lucide-react';
import ManualAttendanceModal from './ManualAttendanceModal';

export default function AttendanceLogs() {
  const [records, setRecords] = useState([]);
  const [dateFilter, setDateFilter] = useState(new Date().toISOString().split('T')[0]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [isManualOpen, setIsManualOpen] = useState(false);

  const fetchRecords = async (targetDate = dateFilter) => {
    try {
      setLoading(true);
      let url = '/api/attendance?';
      if (targetDate) url += `date=${encodeURIComponent(targetDate)}&`;
      if (search) url += `search=${encodeURIComponent(search)}`;

      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        setRecords(data.records || []);
      }
    } catch (err) {
      console.error('Failed to fetch attendance logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords(dateFilter);
  }, [dateFilter, search]);

  const handleShowAll = () => {
    setDateFilter('');
    fetchRecords('');
  };

  const handleExport = (type) => {
    const url = `/api/reports/export?type=${type}&date=${dateFilter || ''}`;
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Daily Attendance Records & Logs</h1>
          <p className="text-sm text-slate-400 mt-1">
            Filter attendance sessions, perform administrative overrides, and export official spreadsheets.
          </p>
        </div>

        <button
          onClick={() => setIsManualOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-600/30 transition transform active:scale-95"
        >
          <UserCheck className="w-4 h-4" />
          + Manual Attendance Override
        </button>
      </div>

      {/* Control & Filter Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md space-y-4">
        
        {/* Row 1: Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            
            {/* Date Picker */}
            <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 border border-slate-800 rounded-xl">
              <Calendar className="w-4 h-4 text-indigo-400" />
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="bg-transparent text-white text-xs outline-none"
              />
            </div>

            <button
              onClick={() => fetchRecords(dateFilter)}
              className="px-3.5 py-2 rounded-xl bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white border border-indigo-500/30 text-xs font-semibold transition"
            >
              Filter Date
            </button>

            <button
              onClick={handleShowAll}
              className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white text-xs font-semibold transition"
            >
              Show All Dates
            </button>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search student or roll no..."
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>

        {/* Row 2: Export Action Buttons */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleExport('daily_excel')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600 hover:text-white transition font-semibold"
            >
              <Download className="w-3.5 h-3.5" />
              Export Daily (.xlsx)
            </button>

            <button
              onClick={() => handleExport('daily_csv')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600/15 text-teal-400 border border-teal-500/30 hover:bg-teal-600 hover:text-white transition font-semibold"
            >
              <Download className="w-3.5 h-3.5" />
              Export Daily (CSV)
            </button>
          </div>

          <span className="text-slate-400">
            Total Logged Check-ins: <strong className="text-white">{records.length}</strong>
          </span>
        </div>

      </div>

      {/* Records Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Log ID</th>
                <th className="py-3.5 px-4">Student ID</th>
                <th className="py-3.5 px-4">Roll No</th>
                <th className="py-3.5 px-4">Student Name</th>
                <th className="py-3.5 px-4">Department</th>
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4">Check-In Time</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {loading ? (
                <tr>
                  <td colSpan="9" className="py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
                    Fetching attendance records...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan="9" className="py-12 text-center text-slate-500">
                    <ClipboardCheck className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    No attendance logs found for the selected criteria.
                  </td>
                </tr>
              ) : (
                records.map((r) => (
                  <tr key={r.attendance_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-4 font-mono text-slate-400">
                      #{r.attendance_id}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-400">
                      {r.student_id}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-medium text-indigo-400">
                      {r.roll_no}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-white">
                      {r.name}
                    </td>
                    <td className="py-3.5 px-4">{r.department}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-400">{r.date}</td>
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-300">{r.time}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        {r.status || 'Present'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono font-semibold text-indigo-400">
                      {Math.round(r.confidence_score || 0)}%
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Attendance Override Modal */}
      {isManualOpen && (
        <ManualAttendanceModal
          onClose={() => setIsManualOpen(false)}
          onSuccess={() => fetchRecords(dateFilter)}
        />
      )}

    </div>
  );
}
