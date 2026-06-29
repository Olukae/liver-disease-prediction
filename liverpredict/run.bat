@echo off
echo [setup] Creating virtual environment...
python -m venv venv

echo [setup] Activating environment...
call venv\Scripts\activate

echo [setup] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [db] Initializing database...
python -c "from app import create_app; create_app(); print('[db] Database ready.')"

echo ======================================
echo LiverPredict AI -- http://localhost:5000
echo ======================================

python app.py

pause