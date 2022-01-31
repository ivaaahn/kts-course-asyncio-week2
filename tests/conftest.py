import asyncio
import http
import os
import urllib

import pytest

from app.car_rent import BOOKED_CARS


def send_ok_result():
    result_url = urllib.parse.urlparse(os.environ["RESULT_URL"])
    conn = http.client.HTTPSConnection(result_url.netloc)
    payload = ""
    headers = {
        "X-Progress-Token": os.environ["PROGRESS_TOKEN"],
    }
    conn.request("POST", "/api/v2.chunk.set_mercury_task_result", payload, headers)
    res = conn.getresponse()

    print("\n")
    if res.status == 200:
        print("=== success result has been saved successfully ===")
    else:
        data = res.read()
        print(data.decode("utf-8"))


def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        try:
            send_ok_result()
        except:
            pass


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


@pytest.fixture
def user_id() -> int:
    return 1


@pytest.fixture(autouse=True)
def clear_booked_cars():
    BOOKED_CARS.clear()
