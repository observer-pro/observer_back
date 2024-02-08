import pytest_asyncio
from socketio import AsyncClient


async def client_generator():
    user = AsyncClient()
    await user.connect('http://127.0.0.1:5000')
    yield user
    await user.disconnect()


@pytest_asyncio.fixture
async def host():
    yield await client_generator().__anext__()


@pytest_asyncio.fixture
async def client():
    yield await client_generator().__anext__()


@pytest_asyncio.fixture
async def events(client, host):
    all_events = {}

    async def event_handler(event, data):
        all_events[event] = data

    client.on('*', event_handler)
    host.on('*', event_handler)

    yield all_events


class TestContext:
    __test__ = False

    def __init__(self):
        self.room_id = 0
        self.host_id = 0
        self.client_id = 0


@pytest_asyncio.fixture(scope='session', autouse=True)
async def context():
    return TestContext()
