
# app/fix_pydantic.py
from __future__ import annotations
import importlib, sys, subprocess

NEEDED = "pydantic>=2.6,<3"

def _install(spec: str):
    subprocess.check_call([sys.executable, "-m", "pip", "install", spec])

def ensure():
    """
    1) Pastikan pydantic v2.x terpasang.
    2) Jika simbol 'with_config' tidak ada (beberapa build Replit), sediakan shim no-op.
    """
    try:
        import pydantic as p
    except Exception:
        _install(NEEDED)
        import pydantic as p  # type: ignore

    # kalau versi tidak sesuai, coba upgrade
    try:
        v = getattr(p, "__version__", "0")
        major = int(str(v).split(".")[0])
        if major < 2:
            _install(NEEDED)
            import pydantic as p  # type: ignore
    except Exception:
        pass

    # shim with_config bila hilang
    if not hasattr(p, "with_config"):
        def with_config(*args, **kwargs):
            """
            Shim no-op untuk kompatibilitas:
            - Bisa dipanggil sebagai decorator: @with_config(...).
            - Mengembalikan objek/dekorasi apa adanya.
            """
            def _decorator(obj):
                return obj
            return _decorator
        setattr(p, "with_config", with_config)
