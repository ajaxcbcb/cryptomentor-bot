
#!/usr/bin/env python3
"""
User Aggregation Module - Combines users from multiple sources
Handles Supabase, old backup, and local storage aggregation
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime

def _load_old_backup() -> List[Dict[str, Any]]:
    """Load premium users from JSON backup"""
    backup_file = "premium_users_backup_20250802_130229.json"
    if not os.path.exists(backup_file):
        return []
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('premium_users', [])
    except Exception:
        return []

def _normalize_old_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize old backup record to standard format"""
    try:
        telegram_id = int(record.get('telegram_id', 0))
        if telegram_id <= 0:
            return {}
        
        return {
            'telegram_id': telegram_id,
            'first_name': record.get('first_name', ''),
            'username': record.get('username', ''),
            'is_premium': bool(record.get('is_premium', 0)),
            'premium_until': record.get('subscription_end'),
            'banned': False,  # Assume not banned from backup
            'credits': 1000,  # Default for premium users
        }
    except Exception:
        return {}

def sb_list_users(filters: Dict[str, str]) -> List[Dict[str, Any]]:
    """Query Supabase users with filters"""
    try:
        from app.supabase_conn import supabase_list_users
        return supabase_list_users(filters)
    except Exception:
        return []

def load_users() -> Dict[str, Any]:
    """Load users from local storage"""
    try:
        from app.storage_local import load_users as load_local
        return load_local()
    except Exception:
        return {}

def list_supabase_lifetime(limit: int = 2000, offset: int = 0) -> Dict[int, Dict[str, Any]]:
    """Get lifetime users from Supabase"""
    out: Dict[int, Dict[str, Any]] = {}
    rows = sb_list_users({
        "is_premium": "eq.true",
        "banned": "eq.false",
        "subscription_end": "is.null",
        "limit": str(limit),
        "offset": str(offset),
    })
    
    for r in rows:
        tid = r.get("telegram_id")
        if tid is None:
            continue
        out[int(tid)] = {
            "telegram_id": int(tid),
            "is_premium": True,
            "premium_until": None,   # lifetime
            "banned": False,
            "source": "supabase",
            "credits": int(r.get("credits", 0) or 0),
        }
    return out

def list_old_lifetime() -> Dict[int, Dict[str, Any]]:
    """Get lifetime users from old backup"""
    out: Dict[int, Dict[str, Any]] = {}
    for r in _load_old_backup():
        m = _normalize_old_record(r)
        if not m:
            continue
        if m["banned"]:
            continue
        
        # lifetime if premium_until is None/"" OR has lifetime flag
        if (m.get("is_premium") and (m.get("premium_until") in (None, "", "null"))) or \
           (str(r.get("plan","")).lower().find("lifetime") >= 0) or bool(r.get("lifetime")):
            out[m["telegram_id"]] = {
                **m,
                "is_premium": True,
                "premium_until": None,
                "source": "old",
            }
    return out

def aggregated_lifetime() -> Dict[int, Dict[str, Any]]:
    """Merge lifetime users from all sources"""
    sup = list_supabase_lifetime()
    old = list_old_lifetime()

    # Optional: lifetime from storage_local
    loc = {}
    try:
        users = load_users()
        for k, v in users.items():
            try: 
                tid = int(k)
            except: 
                continue
            if v.get("banned"): 
                continue
            if bool(v.get("is_premium")) and v.get("premium_until") in (None, "", "null"):
                loc[tid] = {
                    "telegram_id": tid,
                    "is_premium": True,
                    "premium_until": None,
                    "banned": False,
                    "source": "local",
                    "credits": int(v.get("credits", 0) or 0),
                }
    except Exception:
        pass

    merged: Dict[int, Dict[str, Any]] = {}
    def _merge(dst, src):
        if not dst: 
            return src.copy()
        # credits keep max
        dst["credits"] = max(int(dst.get("credits",0)), int(src.get("credits",0)))
        dst["source"] = "merge"
        return dst

    for d in (old, loc, sup):
        for tid, rec in d.items():
            merged[tid] = _merge(merged.get(tid, {}), rec)

    return merged

def aggregated_premium_active() -> tuple[Dict[int, Dict[str, Any]], Dict[str, int]]:
    """Get all active premium users with statistics"""
    stats = {"supabase": 0, "old": 0, "local": 0, "total": 0}
    merged = {}
    
    # Supabase active premium
    supabase_rows = sb_list_users({
        "is_premium": "eq.true",
        "banned": "eq.false",
        "limit": "2000"
    })
    
    for r in supabase_rows:
        tid = r.get("telegram_id")
        if tid:
            merged[int(tid)] = {
                "telegram_id": int(tid),
                "is_premium": True,
                "source": "supabase"
            }
            stats["supabase"] += 1
    
    # Old backup active
    for r in _load_old_backup():
        m = _normalize_old_record(r)
        if m and m.get("is_premium") and not m.get("banned"):
            tid = m["telegram_id"]
            if tid not in merged:
                merged[tid] = {**m, "source": "old"}
                stats["old"] += 1
    
    stats["total"] = len(merged)
    return merged, stats
