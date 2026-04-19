from __future__ import annotations

import asyncio


class Scheduler:
    def __init__(self, scan_service):
        self.scan_service = scan_service
        self._task: asyncio.Task | None = None

    async def start(self):
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self.scan_service.scan_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
