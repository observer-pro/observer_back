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


#
@pytest_asyncio.fixture
async def room_update(host: AsyncClient):
    response = {}

    @host.on('room/update')
    async def room_data(data):
        response.update(data)

    return response


@pytest_asyncio.fixture
async def room_join(client: AsyncClient):
    response = {}

    @client.on('room/join')
    async def room_data(data):
        response.update(data)

    return response


@pytest_asyncio.fixture
async def signal(client: AsyncClient):
    response = {}

    @client.on('room/join')
    async def room_data(data):
        response.update(data)

    return response


@pytest_asyncio.fixture
async def message_to_client(client: AsyncClient):
    response = {}

    @client.on('message/to_client')
    async def room_data(data):
        response.update(data)

    return response


@pytest_asyncio.fixture
async def message_to_mentor(host: AsyncClient):
    response = {}

    @host.on('message/to_mentor')
    async def room_data(data):
        response.update(data)

    return response


@pytest_asyncio.fixture
async def error(host: AsyncClient):
    response = {}

    @host.on('error')
    async def room_data(data):
        response.update(data)

    return response
