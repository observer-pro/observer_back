import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext


async def test_host_sharing_start(host: AsyncClient, client: AsyncClient, events: dict, context: TestContext):
    """Test sharing/start  event"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.01)
    room_update = events.get('room/update')
    await client.emit('room/join', data={'room_id': room_update['id'], 'name': 'John Test'})
    await asyncio.sleep(0.01)

    context.client_id = events['room/join']['user_id']
    context.room_id = events['room/join']['room_id']
    context.host_id = events['room/update']['host']

    await host.emit('sharing/start', data={'room_id': context.room_id, 'user_id': context.client_id})
    await asyncio.sleep(0.01)

    assert events.get('sharing/start') == {}


async def test_sharing_code(host: AsyncClient, client: AsyncClient, events: dict, context: TestContext):
    await host.emit('room/rehost', data={'user_id': context.host_id, 'room_id': context.room_id})
    await asyncio.sleep(0.01)
    await client.emit(
        'room/rejoin',
        data={'room_id': context.room_id, 'user_id': context.client_id},
    )
    await asyncio.sleep(0.01)

    data = {
        'room_id': context.room_id,
        'user_id': context.client_id,
        'files': [
            {'filename': 'main.py', 'status': 'CREATED', 'content': 'содержимое main.py'},
            {'filename': 'data/data.json', 'status': 'CREATED', 'content': 'содержимое data.json'},
        ],
    }
    await client.emit('sharing/code_send', data=data)
    await asyncio.sleep(0.01)

    assert events.get('sharing/code_send') == data

    updated_data = {
        'room_id': context.room_id,
        'user_id': context.client_id,
        'files': [{'filename': 'main.py', 'status': 'UPDATED', 'content': 'содержимое main.py обновилось'}],
    }
    await client.emit('sharing/code_update', data=updated_data)
    await asyncio.sleep(0.01)

    assert events.get('sharing/code_update') == updated_data
