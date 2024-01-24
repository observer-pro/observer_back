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


def create_response_fixture(user, event_name, type_of_data='dict'):
    response = {} if type_of_data == 'dict' else []

    @user.on(event_name)
    async def handle_event(data):
        nonlocal response
        if type_of_data == 'dict':
            response.update(data)
        else:
            response.extend(data)

    return response


@pytest_asyncio.fixture
async def room_update(host: AsyncClient):
    return create_response_fixture(host, 'room/update')


@pytest_asyncio.fixture
async def room_join(client: AsyncClient):
    return create_response_fixture(client, 'room/join')


@pytest_asyncio.fixture
async def room_closed(client: AsyncClient):
    return create_response_fixture(client, 'room/closed')


@pytest_asyncio.fixture
async def settings(client: AsyncClient):
    return create_response_fixture(client, 'settings')


@pytest_asyncio.fixture
async def steps_all(client: AsyncClient):
    return create_response_fixture(client, 'steps/all', type_of_data='list')


@pytest_asyncio.fixture
async def steps_table(host: AsyncClient):
    return create_response_fixture(host, 'steps/table', type_of_data='list')


@pytest_asyncio.fixture
async def steps_to_mentor(host: AsyncClient):
    return create_response_fixture(host, 'steps/status/to_mentor')


@pytest_asyncio.fixture
async def steps_to_client(client: AsyncClient):
    return create_response_fixture(client, 'steps/status/to_client')


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
