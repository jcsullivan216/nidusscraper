from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

import aiofiles  # type: ignore

from .config import MANIFEST, logger


async def save_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


async def retry(
    func: Callable[[], Awaitable[Any]], attempts: int = 3, base_delay: float = 1.0
) -> Any:
    exc: Exception | None = None
    for i in range(attempts):
        try:
            return await func()
        except Exception as e:  # noqa: BLE001
            exc = e
            delay = base_delay * 2**i
            logger.warning("Retry %s/%s after %.1fs due to %s", i + 1, attempts, delay, e)
            await asyncio.sleep(delay)
    raise exc if exc else RuntimeError("Retry failed")


async def update_manifest(path: Path, source_url: str) -> None:
    sha = hash_file(path)
    downloaded_at = datetime.utcnow().isoformat()
    exists = MANIFEST.exists()
    rows = []
    if not exists:
        rows.append(["filename", "sha256", "source_url", "downloaded_at"])
    rows.append([str(path), sha, source_url, downloaded_at])
    async with aiofiles.open(MANIFEST, "a") as f:
        for row in rows:
            line = ",".join(row) + "\n"
            await f.write(line)
