import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, CheckCircle, RefreshCw, AlertCircle } from 'lucide-react';

export default function FaceCaptureModal({ student, onClose, onTrainingComplete }) {
  const [capturing, setCapturing] = useState(false);
  const [count, setCount] = useState(0);
  const [maxCount] = useState(60);
  const [completed, setCompleted] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Position your face in the center of the camera.');
  const [cameraError, setCameraError] = useState('');

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const captureLoopRef = useRef(null);

  // Start Browser Camera
  useEffect(() => {
    let active = true;

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: 'user' }
        });
        if (!active) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      } catch (err) {
        console.error('Camera access error:', err);
        setCameraError('Could not access camera. Please allow camera access in browser permissions.');
      }
    };

    startCamera();

    return () => {
      active = false;
      stopCamera();
    };
  }, []);

  const stopCamera = () => {
    if (captureLoopRef.current) {
      clearInterval(captureLoopRef.current);
      captureLoopRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const handleStartCapture = () => {
    setCapturing(true);
    setStatusMessage('Collecting face samples... Turn head slightly left and right.');

    let currentCount = 0;
    let isProcessing = false;

    captureLoopRef.current = setInterval(async () => {
      if (isProcessing || !videoRef.current || videoRef.current.readyState < 2) return;

      isProcessing = true;
      try {
        const video = videoRef.current;
        const canvas = canvasRef.current || document.createElement('canvas');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const base64Image = canvas.toDataURL('image/jpeg', 0.8);

        const res = await fetch('/api/capture_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: student.student_id,
            image: base64Image
          })
        });
        const data = await res.json();

        if (data.success) {
          currentCount = data.count;
          setCount(currentCount);

          if (data.completed) {
            clearInterval(captureLoopRef.current);
            setCapturing(false);
            setCompleted(true);
            setStatusMessage(`All 60 samples captured! Model trained: ${data.train_msg || 'Success'}`);
            if (onTrainingComplete) onTrainingComplete();
          }
        } else if (data.status === 'NO_FACE') {
          setStatusMessage('No face detected. Look directly into the camera.');
        } else if (data.status === 'MULTIPLE_FACES') {
          setStatusMessage('Multiple faces detected! Please ensure only one person is in frame.');
        }
      } catch (err) {
        console.error('Frame capture error:', err);
      } finally {
        isProcessing = false;
      }
    }, 180); // ~5-6 samples per second -> takes ~10 seconds to collect 60 samples
  };

  const pct = Math.min(100, Math.round((count / maxCount) * 100));

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
            onClick={() => {
              stopCamera();
              onClose();
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Canvas Container */}
        <div className="p-6 space-y-4">
          <div className="relative aspect-[4/3] w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center shadow-inner">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            <canvas ref={canvasRef} className="hidden" />

            {/* Target Reticle */}
            <div className="absolute inset-0 pointer-events-none border border-indigo-500/20 rounded-xl m-6 flex flex-col justify-between p-4">
              <div className="flex justify-between">
                <div className="w-6 h-6 border-t-2 border-l-2 border-indigo-400"></div>
                <div className="w-6 h-6 border-t-2 border-r-2 border-indigo-400"></div>
              </div>
              <div className="flex justify-between">
                <div className="w-6 h-6 border-b-2 border-l-2 border-indigo-400"></div>
                <div className="w-6 h-6 border-b-2 border-r-2 border-indigo-400"></div>
              </div>
            </div>

            {cameraError && (
              <div className="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center p-6 text-center text-rose-400">
                <AlertCircle className="w-10 h-10 mb-2" />
                <p className="text-xs font-semibold">{cameraError}</p>
              </div>
            )}
          </div>

          {/* Progress Bar & Status Text */}
          <div>
            <div className="flex justify-between text-xs mb-1.5 font-medium">
              <span className="text-slate-300">{statusMessage}</span>
              <span className="text-indigo-400 font-mono font-bold">
                {count} / {maxCount} ({pct}%)
              </span>
            </div>
            <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-200"
                style={{ width: `${pct}%` }}
              ></div>
            </div>
          </div>

          {/* Completion Card */}
          {completed && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-3">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <span>
                <strong>Sample Capture Complete!</strong> 60 facial samples collected and LBPH model trained for {student.name}.
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                stopCamera();
                onClose();
              }}
              className="px-4 py-2.5 rounded-xl border border-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition"
            >
              {completed ? 'Done & Close' : 'Cancel'}
            </button>

            {!completed && (
              <button
                type="button"
                onClick={handleStartCapture}
                disabled={capturing || !!cameraError}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50 flex items-center gap-2"
              >
                {capturing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Capturing ({count}/60)...
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
