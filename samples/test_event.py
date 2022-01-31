import asyncio
from asyncio import Event

import pytest

pytestmark = pytest.mark.asyncio


# TODO реализовать функцию цыполнения короутин
async def do_until_event(
    aw: list[asyncio.Task], event: asyncio.Event, timeout: float = None
):
    pass


async def test():
    stop_event = Event()
    stop_event.set()

    async def set_event(event: Event):
        await asyncio.sleep(1)
        event.set()

    async def worker():
        while True:
            await asyncio.sleep(1)

    coros = [*[worker() for i in range(10)], set_event(stop_event)]
    await asyncio.wait_for(
        do_until_event(coros, event=stop_event),
        timeout=1.2,
    )
