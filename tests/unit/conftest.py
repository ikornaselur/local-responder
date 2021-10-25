import pytest

import aiohttp

@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session
