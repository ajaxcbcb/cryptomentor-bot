
import importlib, subprocess, sys

REQS = ["pydantic>=2.6,<3", "pydantic-core>=2.16"]

def _pip(x): 
    subprocess.check_call([sys.executable, "-m", "pip", "install", x])

def ensure():
    try:
        import pydantic as p
    except Exception:
        for r in REQS: 
            _pip(r)
        import pydantic as p  # type: ignore
    
    try:
        version = getattr(p, "__version__", "0")
        major = int(str(version).split(".")[0])
        if major < 2:
            for r in REQS: 
                _pip(r)
            import pydantic as p  # type: ignore
    except Exception:
        pass
    
    # Shim 'with_config' jika belum ada
    if not hasattr(p, "with_config"):
        def with_config(*a, **k):
            def _d(obj): 
                return obj
            return _d
        setattr(p, "with_config", with_config)
