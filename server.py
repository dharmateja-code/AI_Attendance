"""
server.py - High-Performance REST API & Computer Vision Stream Backend for React.js Dashboard.
Integrates OpenCV Face Recognition, Database operations, and Real-Time MJPEG Streaming.
"""

import os
import glob
import time
import base64
from datetime import datetime
import cv2
import numpy as np
from flask import Flask, request, jsonify, Response, send_file, send_from_directory
from flask_cors import CORS
from PIL import Image

def decode_base64_image(base64_str):
    """Decodes a base64 string to an OpenCV BGR image."""
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    img_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

# Import existing modules
from database import db
from face_capture import face_manager, DATASET_DIR, CLASSIFIER_PATH
from reports import report_engine, REPORTS_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global Camera & Recognition Stream Management
class VideoStreamManager:
    """Manages thread-safe webcam access for recognition and capture streams."""

    def __init__(self):
        self.cap = None
        self.is_capturing = False
        self.capture_student_id = None
        self.capture_count = 0
        self.capture_max = 60
        self.capture_message = "Ready"

        # Cooldown tracking for attendance recognition
        self.last_recognized_time = {}   # student_id -> timestamp
        self.recent_marked_cache = []    # [{student_id, name, roll_no, time, confidence, status}]

        # Cascades
        local_face = os.path.join(BASE_DIR, "assets", "haarcascade_frontalface_default.xml")
        face_path = local_face if os.path.exists(local_face) else getattr(cv2.data, 'haarcascades', '') + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(face_path)

        local_eye = os.path.join(BASE_DIR, "assets", "haarcascade_eye.xml")
        eye_path = local_eye if os.path.exists(local_eye) else getattr(cv2.data, 'haarcascades', '') + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_path)

        # LBPH Model
        self.clf = None
        self.load_model()

    def load_model(self):
        """Loads trained LBPH model if available."""
        if os.path.exists(CLASSIFIER_PATH):
            try:
                if hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
                    self.clf = cv2.face.LBPHFaceRecognizer_create()
                    self.clf.read(CLASSIFIER_PATH)
                    return True
            except Exception as e:
                print(f"[ERROR] Loading classifier failed: {e}")
        return False

    def get_camera(self):
        """Initializes or returns active camera instance."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
        return self.cap

    def release_camera(self):
        """Releases camera resource."""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def check_anti_spoofing(self, gray_face):
        """Evaluates Laplacian texture variance and ocular presence."""
        laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        is_texture_valid = laplacian_var > 35.0
        eyes = self.eye_cascade.detectMultiScale(gray_face, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
        return is_texture_valid and len(eyes) >= 1, laplacian_var

    def generate_recognition_frames(self):
        """Yields MJPEG frames for live recognition with overlays and attendance marking."""
        cam = self.get_camera()
        if not cam.isOpened():
            while True:
                err_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(err_frame, "Webcam Stream (Cloud Server)", (100, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (56, 189, 248), 2)
                cv2.putText(err_frame, "Connect webcam or run locally for live video", (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (148, 163, 184), 1)
                cv2.putText(err_frame, f"Cloud Time: {datetime.now().strftime('%H:%M:%S')}", (220, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (16, 185, 129), 1)
                _, jpeg = cv2.imencode('.jpg', err_frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                time.sleep(1)

        while True:
            # If capture session is active, yield to capture mode
            if self.is_capturing:
                time.sleep(0.1)
                continue

            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))

            current_epoch = time.time()

            # Ensure model is refreshed
            if self.clf is None:
                self.load_model()

            for (x, y, w, h) in faces:
                face_roi_gray = gray[y:y + h, x:x + w]
                face_resized = cv2.resize(face_roi_gray, (200, 200))

                # Anti-spoofing check
                is_live, var_val = self.check_anti_spoofing(face_roi_gray)
                if not is_live:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 140, 255), 2)
                    cv2.rectangle(frame, (x, y - 30), (x + w, y), (0, 140, 255), cv2.FILLED)
                    cv2.putText(frame, "Spoof Detected", (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                    continue

                if self.clf:
                    student_id, distance = self.clf.predict(face_resized)
                    confidence_pct = max(0, min(100, int(100 - (distance * 0.7))))

                    if distance < 68 and confidence_pct >= 50:
                        student = db.get_student_by_id(student_id)
                        if student:
                            name = student['name']
                            roll = student['roll_no']

                            # Green bounding box
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (16, 185, 129), 2)
                            cv2.rectangle(frame, (x, y - 40), (x + w, y), (16, 185, 129), cv2.FILLED)
                            label = f"{name} ({confidence_pct}%)"
                            cv2.putText(frame, label, (x + 5, y - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

                            # Trigger attendance recording with 5-second cooldown
                            last_time = self.last_recognized_time.get(student_id, 0)
                            if (current_epoch - last_time) > 5.0:
                                self.last_recognized_time[student_id] = current_epoch
                                res_status, msg, _ = db.record_attendance(student_id, confidence_pct)
                                now_str = datetime.now().strftime("%H:%M:%S")

                                item = {
                                    "student_id": student_id,
                                    "name": name,
                                    "roll_no": roll,
                                    "time": now_str,
                                    "confidence": confidence_pct,
                                    "status": "Marked" if res_status == "SUCCESS" else "Already Marked"
                                }
                                self.recent_marked_cache.insert(0, item)
                                self.recent_marked_cache = self.recent_marked_cache[:15]
                        else:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                            cv2.putText(frame, "Unknown ID", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.rectangle(frame, (x, y - 30), (x + w, y), (0, 0, 255), cv2.FILLED)
                        cv2.putText(frame, "Unknown Person", (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                else:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 165, 0), 2)
                    cv2.putText(frame, "Model Not Trained", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)

            # Overlay Status Banner
            cv2.putText(frame, f"LIVE SCANNER | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (56, 189, 248), 2)

            ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ret:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    def generate_capture_frames(self):
        """Yields MJPEG frames while capturing face samples."""
        cam = self.get_camera()
        while self.is_capturing:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(90, 90))

            if len(faces) == 1 and self.capture_student_id is not None:
                (x, y, w, h) = faces[0]
                self.capture_count += 1
                sample_path = os.path.join(DATASET_DIR, f"user.{self.capture_student_id}.{self.capture_count}.jpg")
                face_crop = gray[y:y + h, x:x + w]
                face_resized = cv2.resize(face_crop, (200, 200))
                cv2.imwrite(sample_path, face_resized)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (16, 185, 129), 2)
                cv2.putText(frame, f"Sample: {self.capture_count}/{self.capture_max}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (16, 185, 129), 2)

                if self.capture_count >= self.capture_max:
                    self.is_capturing = False
                    self.capture_message = "Samples collected! Training LBPH model..."
                    db.update_photo_sample_status(self.capture_student_id, "Sample Ready")
                    # Train model
                    success, msg = face_manager.train_classifier()
                    self.load_model()
                    self.capture_message = f"Done! {msg}"
            elif len(faces) > 1:
                cv2.putText(frame, "Multiple faces detected. Keep only 1 face.", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)
            else:
                cv2.putText(frame, "No face detected. Look directly into camera.", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

            ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.04)


stream_mgr = VideoStreamManager()


# ================= API ENDPOINTS =================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."}), 400

    admin = db.verify_admin(username, password)
    if admin:
        return jsonify({
            "success": True,
            "user": {
                "username": admin['username'],
                "full_name": admin['full_name'],
                "email": admin['email']
            }
        })
    return jsonify({"success": False, "message": "Invalid credentials."}), 401


@app.route('/api/recognize_frame', methods=['POST'])
def api_recognize_frame():
    """Processes a single image frame from the browser webcam, runs LBPH recognition & logs attendance."""
    data = request.get_json() or {}
    image_data = data.get('image', '')
    if not image_data:
        return jsonify({"success": False, "message": "No image data provided"}), 400

    try:
        frame = decode_base64_image(image_data)
        if frame is None:
            return jsonify({"success": False, "message": "Failed to decode image"}), 400

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = stream_mgr.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        results = []
        current_epoch = time.time()

        if stream_mgr.clf is None:
            stream_mgr.load_model()

        for (x, y, w, h) in faces:
            face_roi_gray = gray[y:y + h, x:x + w]
            face_resized = cv2.resize(face_roi_gray, (200, 200))

            is_live, var_val = stream_mgr.check_anti_spoofing(face_roi_gray)
            if not is_live:
                results.append({
                    "box": [int(x), int(y), int(w), int(h)],
                    "status": "Spoof",
                    "label": "Spoof Detected",
                    "confidence": 0
                })
                continue

            if stream_mgr.clf:
                student_id, distance = stream_mgr.clf.predict(face_resized)
                confidence_pct = max(0, min(100, int(100 - (distance * 0.7))))

                if distance < 68 and confidence_pct >= 50:
                    student = db.get_student_by_id(student_id)
                    if student:
                        name = student['name']
                        roll = student['roll_no']

                        # Mark attendance with cooldown
                        last_time = stream_mgr.last_recognized_time.get(student_id, 0)
                        status_str = "Recognized"
                        if (current_epoch - last_time) > 4.0:
                            stream_mgr.last_recognized_time[student_id] = current_epoch
                            res_status, msg, _ = db.record_attendance(student_id, confidence_pct)
                            now_str = datetime.now().strftime("%H:%M:%S")

                            status_str = "Marked" if res_status == "SUCCESS" else "Already Marked"
                            item = {
                                "student_id": student_id,
                                "name": name,
                                "roll_no": roll,
                                "time": now_str,
                                "confidence": confidence_pct,
                                "status": status_str
                            }
                            stream_mgr.recent_marked_cache.insert(0, item)
                            stream_mgr.recent_marked_cache = stream_mgr.recent_marked_cache[:15]

                        results.append({
                            "box": [int(x), int(y), int(w), int(h)],
                            "student_id": student_id,
                            "name": name,
                            "roll_no": roll,
                            "confidence": confidence_pct,
                            "status": status_str,
                            "label": f"{name} ({confidence_pct}%)"
                        })
                    else:
                        results.append({
                            "box": [int(x), int(y), int(w), int(h)],
                            "status": "Unknown",
                            "label": "Unknown ID",
                            "confidence": 0
                        })
                else:
                    results.append({
                        "box": [int(x), int(y), int(w), int(h)],
                        "status": "Unknown",
                        "label": "Unknown Person",
                        "confidence": 0
                    })
            else:
                results.append({
                    "box": [int(x), int(y), int(w), int(h)],
                    "status": "NoModel",
                    "label": "Model Not Trained",
                    "confidence": 0
                })

        return jsonify({"success": True, "faces": results, "total_faces": len(faces)})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/capture_frame', methods=['POST'])
def api_capture_frame():
    """Saves a facial sample image received from browser webcam for student dataset."""
    data = request.get_json() or {}
    image_data = data.get('image', '')
    try:
        student_id = int(data.get('student_id'))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid student_id"}), 400

    if not image_data:
        return jsonify({"success": False, "message": "No image data"}), 400

    try:
        frame = decode_base64_image(image_data)
        if frame is None:
            return jsonify({"success": False, "message": "Could not decode frame"}), 400

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = stream_mgr.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

        if len(faces) == 0:
            return jsonify({"success": False, "message": "No face detected in camera", "status": "NO_FACE"}), 200
        if len(faces) > 1:
            return jsonify({"success": False, "message": "Multiple faces detected", "status": "MULTIPLE_FACES"}), 200

        existing_samples = len(glob.glob(os.path.join(DATASET_DIR, f"user.{student_id}.*.jpg")))
        sample_no = existing_samples + 1
        max_samples = 60

        (x, y, w, h) = faces[0]
        face_crop = gray[y:y + h, x:x + w]
        face_resized = cv2.resize(face_crop, (200, 200))
        sample_path = os.path.join(DATASET_DIR, f"user.{student_id}.{sample_no}.jpg")
        cv2.imwrite(sample_path, face_resized)

        trained = False
        train_msg = ""
        if sample_no >= max_samples:
            db.update_photo_sample_status(student_id, "Sample Ready")
            success, train_msg = face_manager.train_classifier()
            stream_mgr.load_model()
            trained = True

        return jsonify({
            "success": True,
            "count": sample_no,
            "max": max_samples,
            "completed": sample_no >= max_samples,
            "trained": trained,
            "train_msg": train_msg,
            "box": [int(x), int(y), int(w), int(h)]
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    stats = db.get_dashboard_summary()
    total = stats['total_students']
    present = stats['present_today']
    turnout = round((present / total * 100), 1) if total > 0 else 0.0

    return jsonify({
        "success": True,
        "stats": {
            "total_students": total,
            "present_today": present,
            "absent_today": stats['absent_today'],
            "turnout_pct": turnout,
            "departments": stats['departments'],
            "today_date": stats['today_date'],
            "db_engine": "MySQL Server (3306)" if db.use_mysql else "Local SQLite Engine",
            "model_ready": os.path.exists(CLASSIFIER_PATH)
        }
    })


@app.route('/api/students', methods=['GET', 'POST'])
def api_students():
    if request.method == 'GET':
        query = request.args.get('search', '').strip().lower()
        students = db.get_all_students()
        if query:
            students = [
                s for s in students if query in str(s['student_id']).lower() or
                query in s['roll_no'].lower() or query in s['name'].lower()
            ]
        return jsonify({"success": True, "students": students})

    elif request.method == 'POST':
        data = request.get_json() or {}
        try:
            s_id = int(data.get('student_id'))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Student ID must be an integer."}), 400

        roll = data.get('roll_no', '').strip()
        name = data.get('name', '').strip()
        dept = data.get('department', '').strip()
        year = data.get('year', '').strip()
        sem = data.get('semester', '').strip()
        gender = data.get('gender', 'Male')
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        if not (roll and name and dept and year):
            return jsonify({"success": False, "message": "All required fields must be filled."}), 400

        success, msg = db.add_student(s_id, roll, name, dept, year, sem, gender, email, phone)
        return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route('/api/students/<int:student_id>', methods=['PUT', 'DELETE'])
def api_student_detail(student_id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        roll = data.get('roll_no', '').strip()
        name = data.get('name', '').strip()
        dept = data.get('department', '').strip()
        year = data.get('year', '').strip()
        sem = data.get('semester', '').strip()
        gender = data.get('gender', 'Male')
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        success, msg = db.update_student(student_id, roll, name, dept, year, sem, gender, email, phone)
        return jsonify({"success": success, "message": msg}), (200 if success else 400)

    elif request.method == 'DELETE':
        success, msg = db.delete_student(student_id)
        if success:
            # Delete dataset photos for this student
            for f in glob.glob(os.path.join(DATASET_DIR, f"user.{student_id}.*.jpg")):
                try:
                    os.remove(f)
                except Exception:
                    pass
            # Retrain model
            face_manager.train_classifier()
            stream_mgr.load_model()
        return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route('/api/attendance', methods=['GET'])
def api_attendance():
    date_filter = request.args.get('date', '').strip() or None
    search_query = request.args.get('search', '').strip().lower()

    records = db.get_attendance_records(date_filter=date_filter)
    if search_query:
        records = [
            r for r in records if search_query in str(r['student_id']).lower() or
            search_query in r['roll_no'].lower() or search_query in r['name'].lower()
        ]
    return jsonify({"success": True, "records": records})


@app.route('/api/attendance/manual', methods=['POST'])
def api_manual_attendance():
    data = request.get_json() or {}
    try:
        s_id = int(data.get('student_id'))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid Student ID."}), 400

    status, msg, student = db.record_attendance(s_id, confidence=100.0)
    return jsonify({"success": status == "SUCCESS", "status": status, "message": msg, "student": student})


@app.route('/api/attendance/recent', methods=['GET'])
def api_recent_attendance():
    return jsonify({"success": True, "recent": stream_mgr.recent_marked_cache})


@app.route('/api/model/train', methods=['POST'])
def api_train_model():
    success, msg = face_manager.train_classifier()
    if success:
        stream_mgr.load_model()
    return jsonify({"success": success, "message": msg})


@app.route('/api/face_capture/start', methods=['POST'])
def api_start_capture():
    data = request.get_json() or {}
    try:
        s_id = int(data.get('student_id'))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Valid Student ID required."}), 400

    stream_mgr.capture_student_id = s_id
    stream_mgr.capture_count = 0
    stream_mgr.is_capturing = True
    stream_mgr.capture_message = "Capturing face samples from webcam..."
    return jsonify({"success": True, "message": f"Capture started for ID {s_id}."})


@app.route('/api/face_capture/status', methods=['GET'])
def api_capture_status():
    return jsonify({
        "success": True,
        "is_capturing": stream_mgr.is_capturing,
        "count": stream_mgr.capture_count,
        "max": stream_mgr.capture_max,
        "message": stream_mgr.capture_message
    })


@app.route('/api/reports/export', methods=['GET'])
def api_export_report():
    report_type = request.args.get('type', 'daily_excel')
    target_date = request.args.get('date', None) or None
    target_month = request.args.get('month', None) or None

    if report_type == 'daily_excel':
        success, path = report_engine.export_daily_report(date_str=target_date, file_format='excel')
    elif report_type == 'daily_csv':
        success, path = report_engine.export_daily_report(date_str=target_date, file_format='csv')
    elif report_type == 'monthly_excel':
        success, path = report_engine.export_monthly_report(year_month=target_month, file_format='excel')
    elif report_type == 'summary_excel':
        success, path = report_engine.export_cumulative_summary(file_format='excel')
    else:
        return jsonify({"success": False, "message": "Invalid report type."}), 400

    if success and os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    return jsonify({"success": False, "message": str(path)}), 400


# Video Streaming Routes
@app.route('/api/video_feed/recognition')
def video_feed_recognition():
    """MJPEG stream for live recognition."""
    return Response(
        stream_mgr.generate_recognition_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/video_feed/capture')
def video_feed_capture():
    """MJPEG stream for dataset capture."""
    return Response(
        stream_mgr.generate_capture_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serves compiled React single-page application."""
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    elif os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
        return send_from_directory(FRONTEND_DIST, "index.html")
    else:
        return jsonify({
            "status": "online",
            "message": "Python API is running on http://localhost:5000. Run 'npm run dev' inside frontend/ to launch React development server."
        })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("==================================================================")
    print("  SMART ATTENDANCE MANAGEMENT SYSTEM - PYTHON REST API SERVER")
    print(f"  Endpoints live on http://0.0.0.0:{port}")
    print("==================================================================")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
