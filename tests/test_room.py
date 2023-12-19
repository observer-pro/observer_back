import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext


async def test_room_create(host: AsyncClient, room_update: dict, context: TestContext):
    """Test room/create by host"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.1)

    user = room_update['users'][0]
    assert user['role'] == 'host'
    assert user['name'] == 'Teacher'

    context.room_id = room_update['id']
    context.host_id = room_update['host']


async def test_room_rehost_join_alerts(
        host: AsyncClient, client: AsyncClient,
        room_join: dict, room_update: dict, alerts: dict,
        context: TestContext,
):
    """
    Test room/rehost by teacher,
    Test room/join and room/leave by user
    Test alerts when user have an outdated version
    """
    await host.emit('room/rehost', data={'user_id': context.host_id, 'room_id': context.room_id})
    await asyncio.sleep(0.1)
    await client.emit(
        'room/join',
        data={'room_id': context.room_id, 'name': 'John Test', 'version': '1.1'},
    )
    await asyncio.sleep(0.1)
    assert 'You have an outdated version of the plugin' in alerts['message']
    assert alerts['type'] == 'WARNING'

    await asyncio.sleep(0.1)
    assert len(room_update['users']) == 2

    user = room_update['users'][1]
    context.client_id = room_join['user_id']
    assert user['id'] == context.client_id
    assert user['room'] == context.room_id
    assert user['role'] == 'client'
    assert user['name'] == 'John Test'


async def test_room_rejoin_leave(
        host: AsyncClient, client: AsyncClient, room_join: dict, room_update: dict, context: TestContext,
):
    """
    Test room/rejoin by student
    """
    await host.emit('room/rehost', data={'user_id': context.host_id, 'room_id': context.room_id})
    await asyncio.sleep(0.1)
    await client.emit(
        'room/rejoin',
        data={'room_id': context.room_id, 'user_id': context.client_id},
    )
    await asyncio.sleep(0.1)

    assert room_join['room_id'] == context.room_id
    assert room_join['user_id'] == context.client_id

    assert len(room_update['users']) == 2

    await client.emit('room/leave', data={'room_id': context.room_id})
    await asyncio.sleep(0.1)
    assert len(room_update['users']) == 1
