from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from aiohttp import ClientSession
from typing import Any, Dict

from .config import DATA_DIR, GITHUB_TOKEN, logger
from .utils import retry, save_file, update_manifest

SEARCH_URL = "https://api.github.com/search/code"
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

EXTENSIONS = ["urdf", "sdf", "xacro"]


async def fetch_search_page(session: ClientSession, ext: str, page: int) -> Dict[str, Any]:
    params = {"q": f"extension:{ext} stars:>5", "page": str(page), "per_page": "100"}
    async with session.get(SEARCH_URL, params=params, headers=HEADERS) as resp:
        resp.raise_for_status()
        data = await resp.json()
        assert isinstance(data, dict)
        return data


def raw_url(html_url: str) -> str:
    return html_url.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/")


async def download_file(session: ClientSession, url: str, dest: Path) -> None:
    async def _get() -> bytes:
        headers = {
            "If-Modified-Since": (datetime.utcnow() - timedelta(days=1)).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        }
        async with session.get(url, headers=headers) as resp:
            if resp.status == 304:
                logger.info("Not modified: %s", url)
                return b""
            resp.raise_for_status()
            return await resp.read()

    content = await retry(_get)
    if content:
        await save_file(dest, content)
        await update_manifest(dest, url)
        logger.info("Saved %s", dest)


async def crawl_github(session: ClientSession, workers: int = 32) -> None:
    tasks: list[asyncio.Task[None]] = []
    sem = asyncio.Semaphore(workers)
    for ext in EXTENSIONS:
        for page in range(1, 11):
            result = await fetch_search_page(session, ext, page)
            items = result.get("items", [])
            if not items:
                break
            for item in items:
                url = raw_url(item["html_url"])
                path = DATA_DIR / "github" / Path(item["path"]).name

                async def worker(u: str = url, p: Path = path) -> None:
                    async with sem:
                        await download_file(session, u, p)

                tasks.append(asyncio.create_task(worker()))
    await asyncio.gather(*tasks)
