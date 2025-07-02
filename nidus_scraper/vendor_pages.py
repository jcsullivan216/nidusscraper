from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup, Tag
from pyppeteer import launch  # type: ignore

from .config import DATA_DIR, logger
from .utils import retry, update_manifest

VENDOR_JSON = Path(__file__).resolve().parent / "vendor_domains.json"
KEYWORDS = {"product", "system", "platform", "solution", "capability", "hardware"}
EXCLUDE = {"blog", "news", "careers", "privacy"}


async def load_vendor_domains(path: Path = VENDOR_JSON) -> dict[str, list[str]]:
    if not path.exists():
        logger.warning("Vendor domains file not found: %s", path)
        return {}
    try:
        data = json.loads(path.read_text())
        assert isinstance(data, dict)
        return {k: list(v) for k, v in data.items()}
    except Exception as exc:  # pragma: no cover - invalid json
        logger.warning("Failed to parse %s: %s", path, exc)
        return {}


def within_domain(url: str, domain: str) -> bool:
    netloc = urlparse(url).netloc
    return netloc.endswith(domain)


def is_candidate(href: str) -> bool:
    lower = href.lower()
    if any(ex in lower for ex in EXCLUDE):
        return False
    return any(kw in lower for kw in KEYWORDS)


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url) as resp:
            if resp.status >= 400:
                logger.warning("Fetch %s failed with %s", url, resp.status)
                return ""
            return await resp.text()
    except Exception as exc:  # pragma: no cover - network
        logger.warning("Error fetching %s: %s", url, exc)
        return ""


def extract_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href_val = a.get("href")
        if not href_val:
            continue
        href = urljoin(base_url, str(href_val))
        links.append(href)
    return links


async def discover_product_pages(
    session: aiohttp.ClientSession,
    seeds: Iterable[str],
    domain: str,
    max_depth: int = 2,
    max_pages: int = 30,
) -> set[str]:
    visited: set[str] = set()
    pages: set[str] = set()

    async def crawl(url: str, depth: int) -> None:
        if url in visited or depth > max_depth or len(pages) >= max_pages:
            return
        visited.add(url)
        html = await fetch_html(session, url)
        if not html:
            return
        if is_candidate(url):
            pages.add(url)
        for link in extract_links(html, url):
            if not within_domain(link, domain):
                continue
            if link in visited:
                continue
            if is_candidate(link):
                await crawl(link, depth + 1)

    for seed in seeds:
        await crawl(seed, 0)
    return pages


async def render_pdf(url: str, dest: Path) -> None:
    async def _render() -> None:
        browser = await launch(handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False)
        page = await browser.newPage()
        await page.goto(url, {"waitUntil": "networkidle2"})
        await page.pdf({"path": str(dest), "printBackground": True})
        await browser.close()

    try:
        await retry(_render)
        await update_manifest(dest, url)
        logger.info("Saved %s", dest)
    except Exception as exc:  # pragma: no cover - browser errors
        logger.warning("Failed to render %s: %s", url, exc)


async def crawl_vendor_pages(session: aiohttp.ClientSession, workers: int = 4) -> None:
    domains = await load_vendor_domains()
    tasks: list[asyncio.Task[None]] = []
    sem = asyncio.Semaphore(workers)
    for domain, seeds in domains.items():
        pages = await discover_product_pages(session, seeds, domain)
        for url in pages:
            path = urlparse(url).path.strip("/").replace("/", "_") or "index"
            dest = DATA_DIR / "html_product_pages" / domain / f"{path}.pdf"

            async def worker(u: str = url, p: Path = dest) -> None:
                async with sem:
                    await render_pdf(u, p)

            tasks.append(asyncio.create_task(worker()))
    await asyncio.gather(*tasks, return_exceptions=True)

