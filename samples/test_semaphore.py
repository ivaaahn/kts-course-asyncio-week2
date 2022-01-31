import asyncio

import pytest

pytestmark = pytest.mark.asyncio

counter = 0

MAX_CNT = 5

sem = None


async def do_request():
    global sem, counter

    if not sem:
        sem = asyncio.Semaphore(MAX_CNT)

    async with sem:
        counter += 1
        if counter > 5:
            await asyncio.sleep(10)
        await asyncio.sleep(0.1)
        counter -= 1


async def test():

    await asyncio.wait_for(
        asyncio.gather(*[do_request() for _ in range(10)]),
        timeout=1.2,
    )
