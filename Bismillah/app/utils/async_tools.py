
import asyncio
from typing import Iterable, Awaitable, List, Any

async def gather_safe(tasks: Iterable[Awaitable[Any]]) -> List[Any]:
    """
    Jalankan semua task async secara concurrent dan kembalikan hasil dalam urutan input.
    Jika ada exception pada salah satu task, hasil indeks tersebut akan berupa exception.
    """
    return await asyncio.gather(*tasks, return_exceptions=True)
