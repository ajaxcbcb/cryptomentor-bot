
# app/bootstrap_deps.py
import importlib
import subprocess
import sys

REQS = [
    ("aiogram", "aiogram==3.4.1"),
    ("httpx", "httpx>=0.24"),
]

def ensure():
    for mod, pip_spec in REQS:
        try:
            importlib.import_module(mod)
        except Exception:
            print(f"Installing {pip_spec}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_spec])

if __name__ == "__main__":
    ensure()
