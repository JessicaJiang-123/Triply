#!/usr/bin/env bash
set -e

echo "🚀 Setting up Triply Dev Environment..."

# Backend deps
if [ -f "backend/requirements.txt" ]; then
  echo "📦 Installing backend dependencies..."
  cd backend
  python -m pip install --upgrade "pip==25.3"
  pip install -r requirements.txt

  if [ -f "config.example.ini" ]; then
    echo "Remember to update config.ini based on config.example.ini..."
    # cp config.example.ini config.ini
  else
    echo "⚠️ No config.example.ini file found — skipping config setup."
  fi

  cd ..
else
  echo "⚠️ No backend/requirements.txt found — skipping backend setup."
fi

# Frontend deps
if [ -f "frontend/package.json" ]; then
  echo "📦 Installing frontend dependencies..."
  cd frontend
  npm ci || npm install

  if [ -f ".example.env" ]; then
    echo "Remember to update .env based on .example.env..."
    # cp .example.env .env
  else
    echo "⚠️ No .example.env file found — skipping .env setup."
  fi

  cd ..
else
  echo "⚠️ No frontend/package.json found — skipping frontend setup."
fi

echo "✅ Dev environment ready!"