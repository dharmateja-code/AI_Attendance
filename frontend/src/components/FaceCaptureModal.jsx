import React, { useState, useEffect } from 'react';
import { Camera, X, CheckCircle, RefreshCw, AlertCircle } from 'lucide-react';

export default function FaceCaptureModal({ student, onClose, onTrainingComplete }) {
  const [capturing, setCapturing] = useState(false);
  const [progress, setProgress] = useState({ count: 0, max: 60, message: 'Ready to capture.' });
  const [completed, setCompleted] = useState(false);
  const [streamActive, setStreamActive] = useState(false);

  // Poll capture status from server
  useEffect(() => {
    let interval;
    if (capturing) {
      interval = setInterval(async () => {
        try {
          const res = await fetch('/api/face_capture/status');
          const data = await res.json();
          if (data.success) {
            setProgress({
              count: data.count,
              max: data.max,
              message: data.message
            });

            if (!data.is_capturing && data.count >= data.max) {
              setCapturing(false);
              setCompleted(true);
              clearInterval(interval);
              if (onTrainingComplete) onTrainingComplete();
            }
          }
        } catch (err) {
          console.error('Error polling capture status:', err);
        }
      }, 350);
    }
    return () => clearInterval(interval);
  }, [capturing]);

  const handleStartCapture = async () => {
    try {
      setCapturing(true);
      setCompleted(false);
      setStreamActive(true);

      const res = await fetch('/api/face_capture/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: student.student_id })
      });
      const data = await res.json();
      if (!data.success) {
        alert(data.message || 'Failed to start capture.');
        setCapturing(false);
      }
    } catch (err) {
      alert('Failed to connect to capture API.');
      setCapturing(false);
    }
  };

  const pct = Math.round((progress.count / progress.max) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Camera className="w-5 h-5 text-indigo-400" />
              Biometric Face Capture
            </h3>
            <p className="text-xs text-slate-400">
              Student: <span className="text-white font-medium">{student.name}</span> (Roll: {student.roll_no} | ID: {student.student_id})
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Canvas Container */}
        <div className="p-6 space-y-4">
          <div className="relative aspect-[4/3] w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
            {streamActive ? (
              <img
                src="/api/video_feed/capture"
                alt="Webcam capture feed"
                className="w-full h-full object-cover"
                onError={() => {
                  console.warn('Capture feed not responding.');
                }}
              />
            ) : (
              <div className="text-center p-8 text-slate-400">
                <Camera className="w-12 h-12 mx-auto mb-2 opacity-30 text-indigo-400" />
                <p className="text-sm font-semibold text-slate-300">Ready to Capture Samples</p>
                <p className="text-xs text-slate-500 mt-1 max-w-xs">
                  Click the button below. The system will crop 60 facial images and train the LBPH model.
                </p>
              </div>
            )}
          </div>

          {/* Progress Bar & Status Text */}
          <div>
            <div className="flex justify-between text-xs mb-1.5 font-medium">
              <span className="text-slate-300">{progress.message}</span>
              <span className="text-indigo-400 font-mono">
                {progress.count} / {progress.max} ({pct}%)
              </span>
            </div>
            <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-300"
                style={{ width: `${pct}%` }}
              ></div>
            </div>
          </div>

          {/* Completion Card */}
          {completed && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-3">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <span>
                <strong>Success!</strong> 60 facial samples collected and LBPH model trained for {student.name}.
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition"
            >
              {completed ? 'Done & Close' : 'Cancel'}
            </button>

            {!completed && (
              <button
                type="button"
                onClick={handleStartCapture}
                disabled={capturing}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50 flex items-center gap-2"
              >
                {capturing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Capturing Samples ({progress.count}/60)...
                  </>
                ) : (
                  <>
                    <Camera className="w-4 h-4" />
                    Start Webcam Capture
                  </>
                )}
              </button>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
