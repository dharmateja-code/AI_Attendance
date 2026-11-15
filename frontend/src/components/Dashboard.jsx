import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserCheck, 
  UserX, 
  TrendingUp, 
  Camera, 
  UserPlus, 
  FileText, 
  Cpu, 
  Database, 
  ShieldCheck, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw
} from 'lucide-react';

export default function Dashboard({ setActiveTab, onRetrainModel, training }) {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [resStats, resRecent] = await Promise.all([
        fetch('/api/dashboard/stats'),
        fetch('/api/attendance/recent')
      ]);
      const dataStats = await resStats.json();
      const dataRecent = await resRecent.json();

      if (dataStats.success) setStats(dataStats.stats);
      if (dataRecent.success) setRecent(dataRecent.recent || []);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 8000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
          <span className="text-sm text-slate-400">Loading Dashboard Metrics...</span>
        </div>
      </div>
    );
  }

  const kpis = [
    {
      title: 'TOTAL REGISTERED',
      value: stats?.total_students ?? 0,
      icon: Users,
      color: 'from-blue-500 to-indigo-600',
      badge: 'Academic Roster',
      badgeColor: 'text-blue-400 bg-blue-500/10 border-blue-500/20'
    },
    {
      title: 'PRESENT TODAY',
      value: stats?.present_today ?? 0,
      icon: UserCheck,
      color: 'from-emerald-500 to-teal-600',
      badge: stats?.today_date || 'Today',
      badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'ABSENT TODAY',
      value: stats?.absent_today ?? 0,
      icon: UserX,
      color: 'from-rose-500 to-red-600',
      badge: 'Pending Check-in',
      badgeColor: 'text-rose-400 bg-rose-500/10 border-rose-500/20'
    },
    {
      title: 'ATTENDANCE TURNOUT',
      value: `${stats?.turnout_pct ?? 0}%`,
      icon: TrendingUp,
      color: 'from-purple-500 to-pink-600',
      badge: 'Daily Rate',
      badgeColor: 'text-purple-400 bg-purple-500/10 border-purple-500/20'
    }
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      
      {/* Header Greeting & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Academic Attendance Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time biometric facial recognition statistics for <span className="text-indigo-400 font-medium">{stats?.today_date}</span>
          </p>
        </div>

        <button
          onClick={fetchDashboardData}
          className="self-start sm:self-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Stats
        </button>
      </div>

      {/* 4 KPI Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur-sm hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    {kpi.title}
                  </span>
                  <span className="text-3xl font-extrabold text-white tracking-tight">
                    {kpi.value}
                  </span>
                </div>
                <div className={`p-3 rounded-xl bg-gradient-to-br ${kpi.color} text-white shadow-md`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/70 flex items-center justify-between text-xs">
                <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${kpi.badgeColor}`}>
                  {kpi.badge}
                </span>
                <span className="text-slate-400">Live Counter</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Action Hub & Live Activity Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Quick Launch Action Cards (2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-sm">
            <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" />
              Core Operations & Workflows
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              
              {/* Tile 1: Live Scanner */}
              <div 
                onClick={() => setActiveTab('scanner')}
                className="group cursor-pointer p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 hover:bg-emerald-950/10 transition flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-3 group-hover:scale-105 transition">
                    <Camera className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-white text-sm group-hover:text-emerald-400 transition">
                    Live Face Scanner
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Open webcam feed to scan students and record daily attendance.
                  </p>
                </div>
                <span className="mt-4 text-xs font-semibold text-emerald-400 flex items-center gap-1">
                  Launch Camera →
                </span>
              </div>

              {/* Tile 2: Student Management */}
              <div 
                onClick={() => setActiveTab('students')}
                className="group cursor-pointer p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-950/10 transition flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mb-3 group-hover:scale-105 transition">
                    <UserPlus className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-white text-sm group-hover:text-indigo-400 transition">
                    Student Registration
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Register students, capture 60 face photos & train biometric model.
                  </p>
                </div>
                <span className="mt-4 text-xs font-semibold text-indigo-400 flex items-center gap-1">
                  Manage Records →
                </span>
              </div>

              {/* Tile 3: Attendance Logs */}
              <div 
                onClick={() => setActiveTab('attendance')}
                className="group cursor-pointer p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-blue-500/50 hover:bg-blue-950/10 transition flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center mb-3 group-hover:scale-105 transition">
                    <FileText className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-white text-sm group-hover:text-blue-400 transition">
                    Attendance Logs
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Inspect daily check-ins, manual override & search records.
                  </p>
                </div>
                <span className="mt-4 text-xs font-semibold text-blue-400 flex items-center gap-1">
                  View Logs →
                </span>
              </div>

            </div>
          </div>

          {/* Department Breakdown */}
          {stats?.departments && stats.departments.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-sm">
              <h2 className="text-base font-bold text-white mb-3">Enrolled Students by Department</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {stats.departments.map((dept, i) => (
                  <div key={i} className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-xl flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-300">{dept.department}</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-400">
                      {dept.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI & System Readiness Status Card */}
          <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-sm">
            <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Biometric Engine & System Health
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-3">
                <Database className="w-5 h-5 text-indigo-400" />
                <div>
                  <span className="text-slate-400 block font-semibold">Active Database</span>
                  <span className="text-white font-medium">{stats?.db_engine}</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-3">
                <Cpu className="w-5 h-5 text-cyan-400" />
                <div>
                  <span className="text-slate-400 block font-semibold">Recognition Algorithm</span>
                  <span className="text-white font-medium">Local Binary Pattern Histograms (LBPH)</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-3">
                <CheckCircle2 className={`w-5 h-5 ${stats?.model_ready ? 'text-emerald-400' : 'text-amber-400'}`} />
                <div>
                  <span className="text-slate-400 block font-semibold">Classifier Status</span>
                  <span className={`font-medium ${stats?.model_ready ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {stats?.model_ready ? 'Trained (classifier.xml ready)' : 'Pending (Capture faces & train)'}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-3">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <div>
                  <span className="text-slate-400 block font-semibold">Anti-Spoofing Filter</span>
                  <span className="text-emerald-400 font-medium">Active (Laplacian Texture + Eye Cascades)</span>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Live Attendance Activity Stream (1 Column) */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-sm flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-400" />
              Live Check-in Stream
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 animate-pulse">
              LIVE
            </span>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto max-h-[520px] pr-1">
            {recent.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-center p-4 text-slate-500">
                <AlertCircle className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-xs">No scan events recorded in this session yet.</p>
                <p className="text-[11px] text-slate-400 mt-1">Open the Face Scanner to begin scanning students.</p>
              </div>
            ) : (
              recent.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between hover:border-slate-700 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-xs border border-indigo-500/30">
                      {item.name.charAt(0)}
                    </div>
                    <div>
                      <span className="font-semibold text-white text-xs block leading-tight">
                        {item.name}
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {item.roll_no} • ID: {item.student_id}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] font-mono text-slate-400 block">
                      {item.time}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                      item.status === 'Marked' 
                        ? 'bg-emerald-500/20 text-emerald-400' 
                        : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {item.status} ({item.confidence}%)
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
}
