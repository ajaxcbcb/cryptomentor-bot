import asyncio
from typing import List, Any, Optional, Coroutine

async def safe_gather(*coroutines, return_exceptions: bool = True) -> List[Any]:
    """
    Safely gather multiple coroutines with error handling
    """
    try:
        results = await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
        return results
    except Exception as e:
        print(f"Error in safe_gather: {e}")
        return [None] * len(coroutines)

async def gather_safe(*coroutines, return_exceptions: bool = True) -> List[Any]:
    """
    Alias for safe_gather - safely gather multiple coroutines with error handling
    """
    return await safe_gather(*coroutines, return_exceptions=return_exceptions)

async def timeout_wrapper(coro: Coroutine, timeout: float = 30.0, default=None):
    """
    Wrap a coroutine with timeout handling
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        print(f"Timeout after {timeout}s")
        return default
    except Exception as e:
        print(f"Error in timeout_wrapper: {e}")
        return default

async def run_with_retry(coro_func, max_retries: int = 3, delay: float = 1.0, *args, **kwargs):
    """
    Run a coroutine function with retry logic
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(coro_func):
                return await coro_func(*args, **kwargs)
            else:
                return coro_func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                print(f"All {max_retries} attempts failed")

    raise last_error if last_error else Exception("Unknown error in retry logic")