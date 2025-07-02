from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

import nidus_scraper.standards as standards


@pytest.mark.asyncio
async def test_crawl_standards_handles_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nidus_scraper.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("nidus_scraper.config.MANIFEST", tmp_path / "sources.csv")
    monkeypatch.setattr(standards, "DATA_DIR", tmp_path)
    monkeypatch.setattr(standards, "STANDARD_URLS", ["https://example.com/bad.pdf"])

    with aioresponses() as m:
        m.get("https://example.com/bad.pdf", status=404)
        async with aiohttp.ClientSession() as session:
            await standards.crawl_standards(session, workers=1)

    assert not (tmp_path / "standards" / "bad.pdf").exists()
