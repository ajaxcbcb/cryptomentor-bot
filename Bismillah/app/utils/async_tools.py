
import asyncio
from typing import Iterable, Awaitable, List, Any

async def gather_safe(tasks: Iterable[Awaitable[Any]]) -> List[Any]:
    """Safely gather async tasks and return results with exceptions"""
    return await asyncio.gather(*tasks, return_exceptions=True)
