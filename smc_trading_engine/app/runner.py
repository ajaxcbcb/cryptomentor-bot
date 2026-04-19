from __future__ import annotations

import asyncio

from app.config.settings import settings
from app.main import build_services


async def main() -> None:
    services = build_services()
    await services.scan_service.scan_loop()


if __name__ == "__main__":
    asyncio.run(main())
