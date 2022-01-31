import asyncio
import concurrent.futures
import datetime

import requests


def blocking_task():
    requests.get('https://docs.python.org/3/')


async def blocking_worker():
    while True:
        blocking_task()


async def async_thread_worker():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        while True:
            await loop.run_in_executor(pool, blocking_task)


async def ticker():
    while True:
        print(datetime.datetime.now())
        await asyncio.sleep(1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(ticker())
    loop.create_task(blocking_worker())
    # loop.create_task(async_thread_worker())
    loop.run_forever()
