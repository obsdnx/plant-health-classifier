#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

if [ ! -f "pumpkin.tflite" ]; then
  echo ""
  echo "ERROR: pumpkin.tflite not found in $(pwd)"
  echo "Copy your model file here, then run this script again."
  exit 1
fi

echo "Starting server on http://0.0.0.0:8000"
python server.py
