import asyncio
import datetime


async def blocking_task():
    counter = 50000000
    while counter > 0:
        counter -= 1
        if counter % 1000 == 0:
            await asyncio.sleep(0)


async def blocking_worker():
    while True:
        await blocking_task()


async def ticker():
    while True:
        print(datetime.datetime.now())
        await asyncio.sleep(1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(ticker())
    loop.create_task(blocking_worker())
    loop.run_forever()
