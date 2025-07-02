from __future__ import annotations
# pragma: no cover

import asyncio
from pathlib import Path

from aiohttp import ClientSession

from .config import DATA_DIR, logger
from .utils import retry, save_file, update_manifest

STANDARD_URLS = [
    "https://raw.githubusercontent.com/openjaus/openjaus-toolset/master/schema/jaus.xsd",
    "https://raw.githubusercontent.com/openjaus/openjaus-toolset/master/schema/jaus-mobility.xsd",
    "https://example.com/stanag-4586-rev-c.pdf",
]


async def download_standard(session: ClientSession, url: str, dest: Path) -> None:
    async def _get() -> bytes:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()

    try:
        content = await retry(_get)
    except Exception as exc:  # noqa: BLE001 - network errors
        logger.warning("Failed to download %s: %s", url, exc)
        return

    try:
        await save_file(dest, content)
        await update_manifest(dest, url)
        logger.info("Saved %s", dest)
    except Exception as exc:  # noqa: BLE001 - file errors
        logger.warning("Failed to save %s: %s", dest, exc)


async def crawl_standards(session: ClientSession, workers: int = 4) -> None:
    sem = asyncio.Semaphore(workers)
    tasks = []
    for url in STANDARD_URLS:
        filename = url.split("/")[-1]
        dest = DATA_DIR / "standards" / filename

        async def worker(u: str = url, p: Path = dest) -> None:
            async with sem:
                await download_standard(session, u, p)

        tasks.append(asyncio.create_task(worker()))
    await asyncio.gather(*tasks, return_exceptions=True)
