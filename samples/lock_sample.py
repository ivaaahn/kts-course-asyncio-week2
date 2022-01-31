import asyncio

counter = 0


# TODO используя Lock не допустить длительного сна
# убирать sleep() или изменять время сна нельзя
async def worker():
    global counter

    await asyncio.sleep(0.1)
    counter += 1
    print(counter)
    if counter > 1:
        await asyncio.sleep(5)
    else:
        await asyncio.sleep(0.1)
    counter -= 1


res = "Успех"


async def main():
    global SUCCESS, res

    try:
        await asyncio.wait_for(
            asyncio.wait([worker(), worker(), worker(), worker()]), timeout=1
        )
    except asyncio.TimeoutError:
        res = "Долгое время выполнения!"


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

print(res)
