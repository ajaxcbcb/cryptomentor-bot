
# app/fix_pydantic.py
from __future__ import annotations
import importlib, subprocess, sys

REQS = [
    "pydantic>=2.6,<3",
    "pydantic-core>=2.16",
]

def _pip(spec: str):
    subprocess.check_call([sys.executable, "-m", "pip", "install", spec])

def ensure():
    try:
        import pydantic as p
    except Exception:
        for spec in REQS: _pip(spec)
        import pydantic as p  # type: ignore

    try:
        v = getattr(p, "__version__", "0")
        major = int(str(v).split(".")[0])
        if major < 2:
            for spec in REQS: _pip(spec)
            import pydantic as p  # type: ignore
    except Exception:
        pass

    # Shim 'with_config' jika belum ada (beberapa build lama Replit)
    if not hasattr(p, "with_config"):
        def with_config(*args, **kwargs):
            def _decorator(obj):
                return obj
            return _decorator
        setattr(p, "with_config", with_config)
