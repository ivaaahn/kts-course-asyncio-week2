import asyncio
from asyncio import Queue, Event, Semaphore, gather, FIRST_COMPLETED, create_task
from collections import defaultdict
from typing import Optional, Any, Dict, Set

from app.const import MAX_PARALLEL_AGG_REQUESTS_COUNT, WORKERS_COUNT


class PipelineContext:
    def __init__(self, user_id: int, data: Optional[Any] = None):
        self._user_id = user_id
        self.data = data

    @property
    def user_id(self):
        return self._user_id


CURRENT_AGG_REQUESTS_COUNT = 0
BOOKED_CARS: Dict[int, Set[str]] = defaultdict(set)


async def get_offers(source: str) -> list[dict]:
    await asyncio.sleep(1)
    return [
        {"url": f"http://{source}/car?id=1", "price": 1_000, "brand": "LADA"},
        {"url": f"http://{source}/car?id=2", "price": 5_000, "brand": "MITSUBISHI"},
        {"url": f"http://{source}/car?id=3", "price": 3_000, "brand": "KIA"},
        {"url": f"http://{source}/car?id=4", "price": 2_000, "brand": "DAEWOO"},
        {"url": f"http://{source}/car?id=5", "price": 10_000, "brand": "PORSCHE"},
    ]


async def get_offers_from_sourses(sources: list[str]) -> list[dict]:
    global CURRENT_AGG_REQUESTS_COUNT

    if CURRENT_AGG_REQUESTS_COUNT >= MAX_PARALLEL_AGG_REQUESTS_COUNT:
        await asyncio.sleep(10.0)

    CURRENT_AGG_REQUESTS_COUNT += 1
    resp = *await asyncio.gather(*[get_offers(source) for source in sources]),
    CURRENT_AGG_REQUESTS_COUNT -= 1

    out = []

    for res in resp:
        out.extend(res)

    return out


async def worker_combine_service_offers(inbound: Queue, outbound: Queue, sem: Semaphore):
    while True:
        ctx: PipelineContext = await inbound.get()

        async with sem:
            ctx.data = await get_offers_from_sourses(ctx.data)

        await outbound.put(ctx)
        inbound.task_done()


async def chain_combine_service_offers(
        inbound: Queue[PipelineContext], outbound: Queue[PipelineContext], **kw
):
    sem = asyncio.Semaphore(MAX_PARALLEL_AGG_REQUESTS_COUNT)

    workers: list[asyncio.Task] = [asyncio.create_task(worker_combine_service_offers(inbound, outbound, sem)) for _ in
                                   range(WORKERS_COUNT)]
    await inbound.join()
    await gather(*workers)


async def chain_filter_offers(
        inbound: Queue,
        outbound: Queue,
        brand: Optional[str] = None,
        price: Optional[int] = None,
        **kw,
):
    while True:
        ctx: PipelineContext = await inbound.get()
        filtered = []
        for item in ctx.data:
            if price is not None and item['price'] > price:
                continue

            if brand is not None and item['brand'] != brand:
                continue

            filtered.append(item)

        ctx.data = filtered
        await outbound.put(ctx)
        inbound.task_done()


async def cancel_book_request(user_id: int, offer: dict):
    await asyncio.sleep(1)
    BOOKED_CARS[user_id].remove(offer.get("url"))


async def book_request(user_id: int, offer: dict, event: Event) -> dict:
    try:
        BOOKED_CARS[user_id].add(offer.get("url"))
        await asyncio.sleep(1)
        if event.is_set():
            event.clear()
        else:
            await event.wait()
    except asyncio.CancelledError:
        await cancel_book_request(user_id, offer)

    return offer


async def worker_combine_book_car(inbound: Queue, outbound: Queue):
    while True:
        ctx: PipelineContext = await inbound.get()

        event = Event()
        event.set()
        finished, unfinished = await asyncio.wait(
            [book_request(ctx.user_id, item, event) for item in ctx.data], return_when=FIRST_COMPLETED
        )

        for task in finished:
            ctx.data = task.result()

        for task in unfinished:
            task.cancel()

        await asyncio.wait(unfinished)

        await outbound.put(ctx)


async def chain_book_car(
        inbound: Queue[PipelineContext], outbound: Queue[PipelineContext], **kw
):
    await gather(asyncio.create_task(worker_combine_book_car(inbound, outbound)) for _ in
                 range(WORKERS_COUNT))


def run_pipeline(inbound: Queue[PipelineContext]) -> Queue[PipelineContext]:
    aggreg_outbound = Queue()
    filtering_outbound = Queue()
    booking_outbound = Queue()

    create_task(chain_combine_service_offers(inbound, aggreg_outbound))
    create_task(chain_filter_offers(aggreg_outbound, filtering_outbound))
    create_task(chain_book_car(filtering_outbound, booking_outbound))

    return booking_outbound
