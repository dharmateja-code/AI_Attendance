@echo off
title Smart Attendance Management System (React + Python)
color 0A

echo ====================================================================
echo   SMART ATTENDANCE MANAGEMENT SYSTEM (REACT.JS + PYTHON REST API)
echo ====================================================================
echo.
echo Starting Python Backend Server...

cd /d "%~dp0"
call .\venv\Scripts\activate

start "" http://localhost:5000
python server.py

pause
