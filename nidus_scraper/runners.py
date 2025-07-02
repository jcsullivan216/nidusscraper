from __future__ import annotations
# pragma: no cover

import argparse
import asyncio
from typing import Iterable

import aiohttp

from .config import logger
from .github import crawl_github
from .vendors import crawl_vendors
from .vendor_pages import crawl_vendor_pages
from .standards import crawl_standards


async def run_crawlers(sources: Iterable[str], workers: int) -> None:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as session:
        if "urdf" in sources:
            await crawl_github(session, workers)
        if "vendor" in sources:
            await crawl_vendors(session, workers)
        if "pages" in sources:
            await crawl_vendor_pages(session, workers)
        if "standards" in sources:
            await crawl_standards(session, workers)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nidus Scraper")
    parser.add_argument(
        "--sources",
        default="urdf,vendor,standards,pages",
        help="Comma separated list of sources to crawl",
    )
    parser.add_argument("--workers", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    logger.info("Crawling sources: %s", sources)
    asyncio.run(run_crawlers(sources, args.workers))


if __name__ == "__main__":
    main()