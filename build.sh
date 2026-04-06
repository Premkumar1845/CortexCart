#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit  # exit on error

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "=== Installing Node.js dependencies ==="
cd frontend
npm install

echo "=== Building React frontend ==="
npm run build
cd ..

echo "=== Build complete ==="
