#!/bin/bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env || true
