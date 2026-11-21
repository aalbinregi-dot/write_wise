#!/bin/bash
# ──────────────────────────────────────────────────────────
#  WriteWise AI — Local Development Startup Script
# ──────────────────────────────────────────────────────────

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/venv"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║         WriteWise AI — Starting Up         ║"
echo "║   Write. Understand. Improve. Grow.        ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check venv
if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment..."
  python3.12 -m venv "$VENV"
fi

source "$VENV/bin/activate"
pip install -r "$ROOT/requirements.txt" -q

# Run migrations
cd "$ROOT/backend"
echo "⚙  Running database migrations..."
python manage.py makemigrations --check 2>/dev/null || python manage.py makemigrations
python manage.py migrate
echo "✅ Database ready"

# Create superuser if needed (non-interactive)
python manage.py shell -c "
from users.models import User
if not User.objects.filter(email='admin@writewise.ai').exists():
    User.objects.create_superuser(username='admin', email='admin@writewise.ai', password='admin123', role='teacher', first_name='Admin')
    print('✅ Admin user created: admin@writewise.ai / admin123')
else:
    print('✅ Admin user already exists')
" 2>/dev/null

# Download NLTK data
python -c "
import nltk
for pkg in ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','stopwords']:
    nltk.download(pkg, quiet=True)
print('✅ NLTK data ready')
"

echo ""
echo "Starting Django backend on http://localhost:8000 ..."
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# Start frontend
cd "$ROOT/frontend"
echo "Starting React frontend on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  WriteWise AI is running!                  ║"
echo "║  Frontend:  http://localhost:5173          ║"
echo "║  Backend:   http://localhost:8000          ║"
echo "║  Admin:     http://localhost:8000/admin    ║"
echo "║  Login:     admin@writewise.ai / admin123  ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT INT TERM
wait
