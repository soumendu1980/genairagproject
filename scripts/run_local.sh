#!/usr/bin/env sh
set -eu

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
