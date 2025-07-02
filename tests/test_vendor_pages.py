import aiohttp
import pytest

from nidus_scraper import vendor_pages


@pytest.mark.asyncio
async def test_discover_product_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    html = '<a href="/product/item">Item</a><a href="/blog/post">Blog</a>'

    async def fake_fetch(session: aiohttp.ClientSession, url: str) -> str:
        return html

    monkeypatch.setattr(vendor_pages, "fetch_html", fake_fetch)

    async with aiohttp.ClientSession() as session:
        pages = await vendor_pages.discover_product_pages(
            session, ["https://example.com"], "example.com", max_depth=1
        )

    assert pages == {"https://example.com/product/item"}

