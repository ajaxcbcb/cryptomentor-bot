#!/usr/bin/env python3
"""
Shared Services Module - Singleton pattern for performance optimization
Provides cached/shared instances of database, API, and other heavy services
"""

import functools
import time
from typing import Optional, Dict, Any

_db_instance = None
_supabase_client = None
_crypto_api_instance = None
_ai_assistant_instance = None
_cache: Dict[str, Any] = {}
_cache_ttl: Dict[str, float] = {}

DEFAULT_CACHE_TTL = 60  # 1 minute default


def get_database():
    """Get shared database instance (singleton pattern)"""
    global _db_instance
    if _db_instance is None:
        from database import Database
        _db_instance = Database()
    return _db_instance


def get_supabase():
    """Get shared Supabase client (lazy load + singleton)"""
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase_client import supabase
            _supabase_client = supabase
        except Exception:
            _supabase_client = None
    return _supabase_client


def get_crypto_api():
    """Get shared crypto API instance (lazy load + singleton)"""
    global _crypto_api_instance
    if _crypto_api_instance is None:
        try:
            from crypto_api import crypto_api
            _crypto_api_instance = crypto_api
        except Exception:
            _crypto_api_instance = None
    return _crypto_api_instance


def get_ai_assistant():
    """Get shared AI assistant instance (lazy load + singleton)"""
    global _ai_assistant_instance
    if _ai_assistant_instance is None:
        try:
            from ai_assistant import AIAssistant
            _ai_assistant_instance = AIAssistant()
        except Exception:
            _ai_assistant_instance = None
    return _ai_assistant_instance


def cache_get(key: str) -> Optional[Any]:
    """Get cached value if not expired"""
    if key in _cache:
        if time.time() < _cache_ttl.get(key, 0):
            return _cache[key]
        else:
            del _cache[key]
            del _cache_ttl[key]
    return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_CACHE_TTL):
    """Set cached value with TTL"""
    _cache[key] = value
    _cache_ttl[key] = time.time() + ttl


def cache_clear(key: str = None):
    """Clear specific key or all cache"""
    global _cache, _cache_ttl
    if key:
        _cache.pop(key, None)
        _cache_ttl.pop(key, None)
    else:
        _cache = {}
        _cache_ttl = {}


def cached(ttl: int = DEFAULT_CACHE_TTL):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            result = cache_get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def get_user_stats_cached(ttl: int = 30):
    """Get user stats with caching"""
    cached_stats = cache_get("user_stats")
    if cached_stats:
        return cached_stats
    
    db = get_database()
    stats = db.get_user_stats()
    cache_set("user_stats", stats, ttl)
    return stats


def get_live_user_count_cached(ttl: int = 30):
    """Get Supabase user count with caching"""
    cached_count = cache_get("supabase_user_count")
    if cached_count is not None:
        return cached_count
    
    try:
        from supabase_client import get_live_user_count
        count = get_live_user_count()
        cache_set("supabase_user_count", count, ttl)
        return count
    except Exception:
        return 0
