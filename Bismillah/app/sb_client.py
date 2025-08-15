
import os
import requests
import time
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
        self.service_key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
        self.rest_url = f"{self.url}/rest/v1" if self.url else ""
        self.timeout = 15
        self.max_retries = 3
        
    def _get_headers(self, prefer: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers
    
    def _validate_env(self) -> Tuple[bool, str]:
        if not self.url:
            return False, "SUPABASE_URL not set in environment"
        if not self.service_key:
            return False, "SUPABASE_SERVICE_KEY not set in environment"
        if "supabase.co" not in self.url:
            return False, f"Invalid SUPABASE_URL: {self.url}"
        return True, "Environment variables valid"
    
    def _retry_request(self, request_func, *args, **kwargs):
        """Retry request up to max_retries times with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return request_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 0.5 * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {e}")
        
        raise last_exception
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Supabase"""
        is_valid, msg = self._validate_env()
        if not is_valid:
            return False, msg
        
        def _test():
            response = requests.get(
                self.rest_url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if response.status_code in [200, 401, 404]:
                return True, f"Connection successful (HTTP {response.status_code})"
            else:
                return False, f"Connection failed (HTTP {response.status_code})"
        
        try:
            return self._retry_request(_test)
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def query_view(self, view_name: str, select: str = "*", params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Query a Supabase view"""
        is_valid, msg = self._validate_env()
        if not is_valid:
            logger.error(f"Environment validation failed: {msg}")
            return None
        
        def _query():
            query_params = {"select": select}
            if params:
                query_params.update(params)
            
            response = requests.get(
                f"{self.rest_url}/{view_name}",
                headers=self._get_headers(),
                params=query_params,
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 206]:
                raise Exception(f"Query failed: HTTP {response.status_code} - {response.text}")
            
            data = response.json()
            return data[0] if isinstance(data, list) and data else None
        
        try:
            return self._retry_request(_query)
        except Exception as e:
            logger.error(f"Failed to query view {view_name}: {e}")
            return None
    
    def execute_rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Execute a Supabase RPC function"""
        is_valid, msg = self._validate_env()
        if not is_valid:
            logger.error(f"Environment validation failed: {msg}")
            return None
        
        def _execute():
            response = requests.post(
                f"{self.rest_url}/rpc/{function_name}",
                headers=self._get_headers(),
                json=params or {},
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"RPC failed: HTTP {response.status_code} - {response.text}")
            
            return response.json()
        
        try:
            return self._retry_request(_execute)
        except Exception as e:
            logger.error(f"Failed to execute RPC {function_name}: {e}")
            return None

# Global instance
supabase_client = SupabaseClient()
