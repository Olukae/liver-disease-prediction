#!/usr/bin/env bash
# =====================================================================
# run.sh — Start LiverPredict AI (Linux / macOS)
# =====================================================================
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "[setup] Creating virtual environment..."
  python3 -m venv venv
fi

echo "[setup] Installing / updating dependencies..."
./venv/bin/pip install --quiet -r requirements.txt

if [ ! -f "ml/liver_model.joblib" ]; then
  echo "[ml] Training liver disease model..."
  ./venv/bin/python ml/train_model.py
fi

echo "[db] Initializing database..."
./venv/bin/python -c "from app import create_app; app=create_app(); print('[db] Database ready.')"

if [ "${SEED:-0}" = "1" ]; then
  echo "[seed] Seeding demo data..."
  ./venv/bin/python seed.py
fi

echo ""
echo "======================================================"
echo "  LiverPredict AI — http://localhost:5000"
echo "  Admin:   admin@liverpredict.ai / Admin@12345"
echo "  Patient: adeola@example.com / Demo@12345  (if seeded)"
echo "======================================================"
echo ""

export FLASK_APP=app.py
export FLASK_ENV=${FLASK_ENV:-development}
./venv/bin/python app.py
