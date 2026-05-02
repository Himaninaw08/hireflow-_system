@echo off
echo ========================================
echo   JOB BOARD ATS - BACKEND SETUP
echo ========================================
echo.

cd /d E:\jobATS\backend

echo Step 1: Clean database...
if exist db.sqlite3 del db.sqlite3

echo Step 2: Apply migrations...
python manage.py makemigrations
python manage.py migrate

echo Step 3: Create test data...
python create_complete_test_data.py

echo Step 4: Start server...
python manage.py runserver

echo.
echo Backend should be running at: http://127.0.0.1:8000/
echo.
pause
