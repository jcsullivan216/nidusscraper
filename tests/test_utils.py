import asyncio
from pathlib import Path

import pytest

from nidus_scraper import utils


def test_hash_and_save(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    content = b"hello"
    asyncio.run(utils.save_file(path, content))
    h = utils.hash_file(path)
    assert len(h) == 64


@pytest.mark.asyncio
async def test_retry_success() -> None:
    async def func() -> int:
        return 1

    result = await utils.retry(func, attempts=2)
    assert result == 1


@pytest.mark.asyncio
async def test_retry_fail() -> None:
    calls = 0

    async def func() -> int:
        nonlocal calls
        calls += 1
        raise ValueError("fail")

    with pytest.raises(ValueError):
        await utils.retry(func, attempts=2, base_delay=0)
    assert calls == 2
