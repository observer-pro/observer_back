import pytest
import socketio


@pytest.fixture(scope='session')
def get_client():
    client = socketio.Client()
    client.connect('http://localhost:5000')
    yield client
    client.disconnect()


@pytest.fixture
def host(get_client):
    return get_client


@pytest.fixture
def client(get_client):
    return get_client
