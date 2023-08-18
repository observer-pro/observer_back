import pytest
import socketio


@pytest.fixture(scope='session')
def host_client():
    client = socketio.Client()
    client.connect('http://localhost:5000')
    yield client
    client.disconnect()


@pytest.fixture
def host(host_client):
    return host_client


@pytest.fixture(scope='session')
def user_client():
    client = socketio.Client()
    client.connect('http://localhost:5000')
    yield client
    client.disconnect()


@pytest.fixture
def client(user_client):
    return user_client


@pytest.fixture
def room_update(host):
    response = {}

    @host.on('room/update')
    def room_data(data):
        response.update(data)

    return response


@pytest.fixture
def room_join(client):
    response = {}

    @client.on('room/join')
    def room_data(data):
        response.update(data)

    return response


@pytest.fixture
def message_to_client(client):
    response = {}

    @client.on('message/to_client')
    def room_data(data):
        response.update(data)

    return response


@pytest.fixture
def message_to_mentor(host):
    response = {}

    @host.on('message/to_mentor')
    def room_data(data):
        response.update(data)

    return response


@pytest.fixture
def error(host):
    response = {}

    @host.on('error')
    def room_data(data):
        response.update(data)

    return response
