import React, { useState, useEffect, useRef } from 'react';
import { 
  Camera, 
  ShieldCheck, 
  Clock, 
  RefreshCw, 
  Info,
  Laptop,
  Server,
  AlertCircle
} from 'lucide-react';

export default function LiveScanner() {
  const [recent, setRecent] = useState([]);
  const [cameraMode, setCameraMode] = useState('browser'); // 'browser' (cloud/client webcam) or 'server' (local OpenCV)
  const [cameraError, setCameraError] = useState('');
  const [isScanning, setIsScanning] = useState(true);
  const [serverStreamKey, setServerStreamKey] = useState(Date.now());
  const [detectionStatus, setDetectionStatus] = useState('Align your face in front of the camera');

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const offscreenCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const recognitionIntervalRef = useRef(null);

  // Poll recent attendance records from backend
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

  useEffect(() => {
    fetchRecent();
    const interval = setInterval(fetchRecent, 1500);
    return () => clearInterval(interval);
  }, []);

  // Initialize Browser Webcam Stream (getUserMedia)
  useEffect(() => {
    if (cameraMode !== 'browser') {
      stopBrowserCamera();
      return;
    }

    startBrowserCamera();

    return () => {
      stopBrowserCamera();
    };
  }, [cameraMode]);

  const startBrowserCamera = async () => {
    setCameraError('');
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API (getUserMedia) not supported in this browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          startRecognitionLoop();
        };
      }
    } catch (err) {
      console.error('Browser camera access error:', err);
      setCameraError(
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Please click the camera icon in your browser URL bar and allow camera access.'
          : 'Could not access webcam: ' + err.message
      );
    }
  };

  const stopBrowserCamera = () => {
    if (recognitionIntervalRef.current) {
      clearInterval(recognitionIntervalRef.current);
      recognitionIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    clearOverlayCanvas();
  };

  const clearOverlayCanvas = () => {
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  };

  // Continuous frame analysis loop
  const startRecognitionLoop = () => {
    if (recognitionIntervalRef.current) clearInterval(recognitionIntervalRef.current);

    let isProcessing = false;

    recognitionIntervalRef.current = setInterval(async () => {
      if (isProcessing || !videoRef.current || videoRef.current.readyState < 2) return;

      isProcessing = true;
      try {
        const video = videoRef.current;
        const videoWidth = video.videoWidth || 640;
        const videoHeight = video.videoHeight || 480;

        // Initialize offscreen capture canvas
        if (!offscreenCanvasRef.current) {
          offscreenCanvasRef.current = document.createElement('canvas');
        }
        const offCanvas = offscreenCanvasRef.current;
        offCanvas.width = videoWidth;
        offCanvas.height = videoHeight;
        const offCtx = offCanvas.getContext('2d');
        offCtx.drawImage(video, 0, 0, videoWidth, videoHeight);

        const base64Image = offCanvas.toDataURL('image/jpeg', 0.7);

        // Send frame to Python AI backend
        const res = await fetch('/api/recognize_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: base64Image })
        });
        const data = await res.json();

        if (data.success && canvasRef.current) {
          renderDetections(data.faces || [], videoWidth, videoHeight);
        }
      } catch (err) {
        console.error('Frame recognition error:', err);
      } finally {
        isProcessing = false;
      }
    }, 380); // ~2.5 requests per second (fast, lightweight, smooth)
  };

  const renderDetections = (faces, videoWidth, videoHeight) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = videoWidth;
    canvas.height = videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, videoWidth, videoHeight);

    if (faces.length === 0) {
      setDetectionStatus('Looking for registered face...');
      return;
    }

    faces.forEach((face) => {
      const [x, y, w, h] = face.box;

      // Color scheme based on status
      let strokeColor = '#10B981'; // Green (Recognized)
      let statusBg = 'rgba(16, 185, 129, 0.85)';
      let label = face.label || 'Student';

      if (face.status === 'Spoof') {
        strokeColor = '#F59E0B'; // Orange
        statusBg = 'rgba(245, 158, 11, 0.9)';
        label = '⚠️ Spoof Screen Suspected';
      } else if (face.status === 'Unknown') {
        strokeColor = '#EF4444'; // Red
        statusBg = 'rgba(239, 68, 68, 0.9)';
        label = 'Unknown Person';
      } else if (face.status === 'NoModel') {
        strokeColor = '#F59E0B';
        statusBg = 'rgba(245, 158, 11, 0.9)';
        label = 'Train Model in Students Tab';
      }

      // Draw bounding box
      ctx.lineWidth = 3;
      ctx.strokeStyle = strokeColor;
      ctx.strokeRect(x, y, w, h);

      // Draw corner brackets
      const cornerLen = 14;
      ctx.lineWidth = 4;
      // Top-Left
      ctx.beginPath();
      ctx.moveTo(x, y + cornerLen);
      ctx.lineTo(x, y);
      ctx.lineTo(x + cornerLen, y);
      ctx.stroke();
      // Top-Right
      ctx.beginPath();
      ctx.moveTo(x + w - cornerLen, y);
      ctx.lineTo(x + w, y);
      ctx.lineTo(x + w, y + cornerLen);
      ctx.stroke();
      // Bottom-Left
      ctx.beginPath();
      ctx.moveTo(x, y + h - cornerLen);
      ctx.lineTo(x, y + h);
      ctx.lineTo(x + cornerLen, y + h);
      ctx.stroke();
      // Bottom-Right
      ctx.beginPath();
      ctx.moveTo(x + w - cornerLen, y + h);
      ctx.lineTo(x + w, y + h);
      ctx.lineTo(x + w, y + h - cornerLen);
      ctx.stroke();

      // Label Badge
      ctx.font = 'bold 14px "Segoe UI", sans-serif';
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = statusBg;
      ctx.fillRect(x, Math.max(0, y - 28), textWidth + 16, 26);

      ctx.fillStyle = '#FFFFFF';
      ctx.fillText(label, x + 8, Math.max(18, y - 10));

      if (face.status === 'Marked') {
        setDetectionStatus(`✅ Attendance Marked: ${face.name} (${face.roll_no})`);
      } else if (face.status === 'Already Marked') {
        setDetectionStatus(`ℹ️ Already Checked-in Today: ${face.name}`);
      } else if (face.status === 'Unknown') {
        setDetectionStatus('⚠️ Unknown face detected. Please register in Students tab.');
      }
    });
  };

  const handleRestartServerStream = () => {
    setServerStreamKey(Date.now());
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Top Banner & Mode Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping"></span>
            Real-Time Face Recognition Scanner
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Stand in front of your camera. The AI detects your facial biometric profile and records daily attendance.
          </p>
        </div>

        {/* Camera Source Selector */}
        <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setCameraMode('browser')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              cameraMode === 'browser'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Laptop className="w-3.5 h-3.5" />
            Browser Camera (Cloud/Local)
          </button>
          <button
            onClick={() => setCameraMode('server')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              cameraMode === 'server'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            Server Camera
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
                {cameraMode === 'browser' ? 'Browser WebRTC Camera Feed' : 'Server Video Stream'}
              </span>
              <span className="ml-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                Anti-Spoof Active
              </span>
              {cameraMode === 'server' && (
                <button
                  onClick={handleRestartServerStream}
                  className="p-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
                  title="Reload stream"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Video Stream Frame */}
          <div className="relative aspect-[4/3] w-full bg-black rounded-xl overflow-hidden border border-slate-800/80 flex items-center justify-center shadow-inner group">
            
            {cameraMode === 'browser' ? (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                <canvas
                  ref={canvasRef}
                  className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                />
              </>
            ) : (
              <img
                key={serverStreamKey}
                src={`/api/video_feed/recognition?t=${serverStreamKey}`}
                alt="Server Video Stream"
                className="w-full h-full object-cover"
                onError={() => {
                  console.warn('Server camera stream error.');
                }}
              />
            )}

            {/* Camera Permission / Error Warning */}
            {cameraError && (
              <div className="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center p-6 text-center text-rose-400">
                <AlertCircle className="w-12 h-12 mb-3 text-rose-500" />
                <h4 className="text-sm font-bold text-white mb-1">Camera Access Required</h4>
                <p className="text-xs max-w-sm mb-4 text-slate-300">{cameraError}</p>
                <button
                  onClick={startBrowserCamera}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg transition"
                >
                  Grant Camera Permission
                </button>
              </div>
            )}
          </div>

          {/* Live Status Subtitle */}
          <div className="mt-3 p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs font-semibold text-center text-indigo-300">
            {detectionStatus}
          </div>

          {/* Legend Strip */}
          <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span>Green Box: Recognized Student</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
              <span>Red Box: Unknown Person</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              <span>Orange: Spoof Attempt</span>
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
                  Align your face in front of the camera. Attendance will appear here instantly.
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
