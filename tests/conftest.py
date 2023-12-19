import pytest_asyncio
from socketio import AsyncClient


@pytest_asyncio.fixture(scope='function')
async def host_client():
    client = AsyncClient()
    await client.connect('http://127.0.0.1:5000')
    yield client
    await client.disconnect()


@pytest_asyncio.fixture
async def host(host_client):
    return host_client


@pytest_asyncio.fixture(scope='function')
async def user_client():
    client = AsyncClient()
    await client.connect('http://127.0.0.1:5000')
    yield client
    await client.disconnect()


@pytest_asyncio.fixture
async def client(user_client):
    return user_client


def create_response_fixture(client, event_name):
    response = {}

    @client.on(event_name)
    async def handle_event(data):
        response.update(data)

    return response


@pytest_asyncio.fixture
async def room_update(host: AsyncClient):
    return create_response_fixture(host, 'room/update')


@pytest_asyncio.fixture
async def room_join(client: AsyncClient):
    return create_response_fixture(client, 'room/join')


@pytest_asyncio.fixture
async def room_rehost(client: AsyncClient):
    return create_response_fixture(client, 'room/rehost')


@pytest_asyncio.fixture
async def room_rejoin(client: AsyncClient):
    return create_response_fixture(client, 'room/rejoin')


@pytest_asyncio.fixture
async def message_to_client(client: AsyncClient):
    return create_response_fixture(client, 'message/to_client')


@pytest_asyncio.fixture
async def message_to_mentor(host: AsyncClient):
    return create_response_fixture(host, 'message/to_mentor')


@pytest_asyncio.fixture
async def get_user_messages(host: AsyncClient):
    return create_response_fixture(host, 'message/user')


@pytest_asyncio.fixture
async def message(client: AsyncClient):
    return create_response_fixture(client, 'message')


@pytest_asyncio.fixture
async def error(host: AsyncClient):
    return create_response_fixture(host, 'error')


@pytest_asyncio.fixture
async def alerts(client: AsyncClient):
    return create_response_fixture(client, 'alerts')


class TestContext:
    __test__ = False

    def __init__(self):
        self.room_id = 0
        self.host_id = 0
        self.client_id = 0


@pytest_asyncio.fixture(scope='session', autouse=True)
async def context():
    return TestContext()
