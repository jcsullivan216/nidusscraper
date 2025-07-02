from __future__ import annotations
# pragma: no cover

import asyncio
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

from aiohttp import ClientSession
from bs4 import BeautifulSoup, Tag

from .config import DATA_DIR, logger
from .utils import retry, save_file, update_manifest

VENDOR_PAGES = [
    "https://www.maxongroup.com/en-us/news-and-events/media-center",
    "https://www.tmotor.com/html/download/",
    "https://raw.githubusercontent.com/ouster-lidar/ouster-sdk/master/doc/README.md",
]


async def fetch_html(session: ClientSession, url: str) -> str:
    try:
        async with session.get(url) as resp:
            if resp.status >= 400:
                logger.warning("Failed to fetch %s: %s", url, resp.status)
                return ""
            return await resp.text()
    except Exception as exc:  # pragma: no cover - network
        logger.warning("Error fetching %s: %s", url, exc)
        return ""


def extract_pdfs(html: str, base_url: str) -> Iterable[str]:
    """Return absolute PDF URLs discovered in ``html``.

    Uses :func:`urllib.parse.urljoin` to handle relative paths and replaces any
    Windows-style backslashes with forward slashes.
    """
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href = a.get("href")
        if not href:
            continue
        href = str(href)
        if href.lower().endswith(".pdf"):
            if not href.startswith("http"):
                href = urljoin(base_url, href)
            href = href.replace("\\", "/")
            links.append(href)
    return links


async def download_pdf(session: ClientSession, url: str, dest: Path) -> None:
    async def _get() -> bytes:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()

    content = await retry(_get)
    await save_file(dest, content)
    await update_manifest(dest, url)
    logger.info("Saved %s", dest)


async def crawl_vendors(session: ClientSession, workers: int = 32) -> None:
    tasks = []
    sem = asyncio.Semaphore(workers)
    for page in VENDOR_PAGES:
        html = await fetch_html(session, page)
        if not html:
            continue
        for pdf in extract_pdfs(html, page):
            filename = pdf.split("/")[-1]
            dest = DATA_DIR / "vendors" / filename

            async def worker(u: str = pdf, p: Path = dest) -> None:
                async with sem:
                    await download_pdf(session, u, p)

            tasks.append(asyncio.create_task(worker()))
    await asyncio.gather(*tasks)