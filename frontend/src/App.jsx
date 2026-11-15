import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import LiveScanner from './components/LiveScanner';
import StudentManagement from './components/StudentManagement';
import AttendanceLogs from './components/AttendanceLogs';
import Reports from './components/Reports';
import { Sparkles, CheckCircle, AlertCircle } from 'lucide-react';

export default function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('admin_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [activeTab, setActiveTab] = useState('dashboard');
  const [training, setTraining] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_user');
    setUser(null);
  };

  const handleRetrainModel = async () => {
    try {
      setTraining(true);
      const res = await fetch('/api/model/train', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast(data.message || 'LBPH Model successfully retrained!', 'success');
      } else {
        showToast(data.message || 'Model retraining failed.', 'error');
      }
    } catch (err) {
      showToast('Network error retraining model.', 'error');
    } finally {
      setTraining(false);
    }
  };

  if (!user) {
    return <Login onLoginSuccess={(u) => setUser(u)} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onLogout={handleLogout}
        onRetrainModel={handleRetrainModel}
        training={training}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard
            setActiveTab={setActiveTab}
            onRetrainModel={handleRetrainModel}
            training={training}
          />
        )}
        {activeTab === 'scanner' && <LiveScanner />}
        {activeTab === 'students' && <StudentManagement />}
        {activeTab === 'attendance' && <AttendanceLogs />}
        {activeTab === 'reports' && <Reports />}
      </main>

      {/* Floating Notification Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div className={`px-4 py-3 rounded-xl border shadow-2xl flex items-center gap-3 text-xs font-semibold backdrop-blur-md ${
            toast.type === 'success'
              ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-300 shadow-emerald-950/50'
              : 'bg-rose-950/90 border-rose-500/40 text-rose-300 shadow-rose-950/50'
          }`}>
            {toast.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{toast.message}</span>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-400">
        <p>Smart Attendance Management System Using Face Recognition • CSE Major Project • React + Python Flask + OpenCV</p>
      </footer>

    </div>
  );
}
