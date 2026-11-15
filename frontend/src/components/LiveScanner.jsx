import React, { useState, useEffect } from 'react';
import { 
  Camera, 
  ShieldCheck, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  Maximize2,
  RefreshCw,
  Info
} from 'lucide-react';

export default function LiveScanner() {
  const [recent, setRecent] = useState([]);
  const [streamActive, setStreamActive] = useState(true);
  const [streamKey, setStreamKey] = useState(Date.now());
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Poll recent attendance records every 1.5 seconds
  useEffect(() => {
    const fetchRecent = async () => {
      try {
        const res = await fetch('/api/attendance/recent');
        const data = await res.json();
        if (data.success) {
          setRecent(data.recent || []);
        }
      } catch (err) {
        console.error('Error fetching recent attendance:', err);
      }
    };

    fetchRecent();
    const interval = setInterval(fetchRecent, 1500);
    return () => clearInterval(interval);
  }, []);

  const handleRestartStream = () => {
    setStreamActive(false);
    setTimeout(() => {
      setStreamKey(Date.now());
      setStreamActive(true);
    }, 200);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping"></span>
            Real-Time Face Recognition Scanner
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Stand in front of the webcam. The system will detect your face, verify anti-spoof liveness, and log attendance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRestartStream}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition shadow-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Reload Stream
          </button>
        </div>
      </div>

      {/* Main Grid: Left Camera feed (2 Cols) | Right Live Stream Feed (1 Col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Camera Container */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-2xl backdrop-blur-md flex flex-col">
          
          {/* Camera Header Status Strip */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-4">
            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Webcam Feed (30 FPS)
              </span>
              <span className="ml-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                Anti-Spoof Protected
              </span>
            </div>
          </div>

          {/* Video Stream Frame */}
          <div className="relative aspect-[4/3] w-full bg-black rounded-xl overflow-hidden border border-slate-800/80 flex items-center justify-center shadow-inner group">
            {streamActive ? (
              <img
                key={streamKey}
                src={`/api/video_feed/recognition?t=${streamKey}`}
                alt="Live Face Recognition Video Stream"
                className="w-full h-full object-cover"
                onError={() => {
                  console.warn('Recognition video stream disconnected.');
                }}
              />
            ) : (
              <div className="text-center p-8 text-slate-500">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-indigo-400" />
                <p className="text-xs">Connecting to camera video stream...</p>
              </div>
            )}

            {/* Target Reticle Overlay */}
            <div className="absolute inset-0 pointer-events-none border border-emerald-500/10 rounded-xl m-4 flex flex-col justify-between p-4">
              <div className="flex justify-between">
                <div className="w-8 h-8 border-t-2 border-l-2 border-emerald-500/50"></div>
                <div className="w-8 h-8 border-t-2 border-r-2 border-emerald-500/50"></div>
              </div>
              <div className="flex justify-between">
                <div className="w-8 h-8 border-b-2 border-l-2 border-emerald-500/50"></div>
                <div className="w-8 h-8 border-b-2 border-r-2 border-emerald-500/50"></div>
              </div>
            </div>
          </div>

          {/* Instructions Strip */}
          <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Green Box: Recognized Student</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              <span>Red Box: Unknown / Unregistered</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              <span>Orange: Screen / Photo Spoof Detected</span>
            </div>
          </div>

        </div>

        {/* Live Attendance Log Sidebar */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-2xl backdrop-blur-md flex flex-col h-full">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Real-Time Feed
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Auto Sync
            </span>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto max-h-[480px] pr-1">
            {recent.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-slate-500">
                <Camera className="w-10 h-10 mb-3 opacity-30 text-indigo-400" />
                <p className="text-xs font-semibold text-slate-400">Scanner Waiting...</p>
                <p className="text-[11px] text-slate-500 mt-1 max-w-[200px]">
                  Align registered student face with camera. Attendance will appear here instantly.
                </p>
              </div>
            ) : (
              recent.map((entry, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-slate-700 transition flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-bold text-xs">
                      {entry.name.charAt(0)}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white block">
                        {entry.name}
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {entry.roll_no}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] font-mono text-slate-400 block">
                      {entry.time}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-md inline-block mt-0.5 ${
                        entry.status === 'Marked'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {entry.status} ({entry.confidence}%)
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Duplicate Prevention Note */}
          <div className="mt-4 p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
            <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <span>
              <strong>Duplicate Prevention Active:</strong> If a student has already scanned today, their record will not be duplicated.
            </span>
          </div>

        </div>

      </div>

    </div>
  );
}
