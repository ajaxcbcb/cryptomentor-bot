
import os, time, requests

REQ_TIMEOUT = 15

def _env():
    url = (os.getenv("SUPABASE_URL") or os.getenv("SUPABASEURL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASESERVICEKEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Supabase env missing (SUPABASE_URL / SUPABASE_SERVICE_KEY)")
    return url, key, f"{url}/rest/v1"

def _headers(key: str, prefer: str | None = None):
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    return h

def _retry(fn, n=3, base=0.6):
    last = None
    for i in range(n):
        try: return fn()
        except Exception as e:
            last = e; time.sleep(base*(2**i))
    raise last

def health_users():
    url, key, rest = _env()
    def _once():
        r = requests.get(f"{rest}/users", headers=_headers(key, "count=exact"),
                         params={"select":"id","limit":"1"}, timeout=REQ_TIMEOUT)
        ok = r.status_code in (200,206)
        total = 0
        cr = r.headers.get("Content-Range","")
        if "/" in cr:
            try: total = int(cr.split("/")[-1])
            except: pass
        return ok, total, f"users_status={r.status_code}"
    return _retry(_once, n=2)

def get_view(view: str):
    url, key, rest = _env()
    def _once():
        r = requests.get(f"{rest}/{view}", headers=_headers(key),
                         params={"select":"*"}, timeout=REQ_TIMEOUT)
        if r.status_code not in (200,206):
            raise RuntimeError(f"GET {view} {r.status_code} {r.text}")
        return r.json()
    return _retry(_once)

def upsert_users(rows):
    url, key, rest = _env()
    def _once():
        r = requests.post(f"{rest}/users",
            headers=_headers(key, "resolution=merge-duplicates,return=representation"),
            params={"on_conflict":"telegram_id"},
            json=rows, timeout=REQ_TIMEOUT)
        if r.status_code not in (200,201):
            raise RuntimeError(f"UPSERT users {r.status_code} {r.text}")
        return r.json() if r.text else []
    return _retry(_once)

def project_url():
    url, key, rest = _env()
    return url
