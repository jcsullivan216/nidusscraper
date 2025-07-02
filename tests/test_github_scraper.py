import asyncio
from pathlib import Path

import pytest
from aioresponses import aioresponses
import aiohttp

from nidus_scraper import github
from nidus_scraper.github import crawl_github, SEARCH_URL, raw_url


@pytest.mark.asyncio
async def test_crawl_github(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nidus_scraper.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("nidus_scraper.config.MANIFEST", tmp_path / "sources.csv")
    monkeypatch.setattr(github, "DATA_DIR", tmp_path)
    tmp_path.mkdir(exist_ok=True)
    search_json = {
        "items": [
            {
                "html_url": "https://github.com/org/repo/blob/main/test.urdf",
                "path": "test.urdf",
            }
        ]
    }

    monkeypatch.setattr(github, "EXTENSIONS", ["urdf"])

    async def fake_fetch(session, ext, page):
        if page == 1:
            return search_json
        return {"items": []}

    monkeypatch.setattr(github, "fetch_search_page", fake_fetch)

    raw_content = b"<robot/>"
    with aioresponses() as m:
        m.get(f"{SEARCH_URL}?q=extension:urdf+stars:>5&page=1&per_page=100", payload=search_json)
        m.get(raw_url("https://github.com/org/repo/blob/main/test.urdf"), status=200, body=raw_content)

        async with asyncio.timeout(5):
            async with aiohttp.ClientSession() as session:
                await crawl_github(session, workers=1)

    saved = tmp_path / "github" / "test.urdf"
    assert saved.exists()
    assert saved.read_bytes() == raw_content
