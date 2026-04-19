#!/bin/bash
set -euo pipefail
uvicorn app.main:app --reload --port ${APP_PORT:-8000}
