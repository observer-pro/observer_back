import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext


async def test_steps_all(
    host: AsyncClient,
    client: AsyncClient,
    room_join: dict,
    room_update: dict,
    steps_all: list,
    context: TestContext,
):
    """Test steps/all event"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.01)
    context.room_id = room_update['id']
    context.host_id = room_update['host']
    await client.emit(
        'room/join',
        data={'room_id': context.room_id, 'name': 'John Test', 'version': '1.1'},
    )
    await asyncio.sleep(0.01)
    context.client_id = room_join['user_id']

    steps = [
        {
            'name': '1',
            'content': 'Content 1',
            'language': 'html',
            'type': 'exercise',
        },
        {
            'name': '2',
            'content': 'Content 2',
            'language': 'html',
            'type': 'exercise',
        },
        {
            'name': '3',
            'content': 'Content 3',
            'language': 'html',
            'type': 'exercise',
        },
    ]
    await host.emit('steps/all', data=steps)
    await asyncio.sleep(0.01)

    assert steps_all == steps


async def test_steps_to_mentor_and_client(
    host: AsyncClient,
    client: AsyncClient,
    steps_to_mentor: dict,
    steps_to_client: dict,
    context: TestContext,
):
    """Test steps/to_mentor and steps/to_client."""
    await host.emit('room/rehost', data={'user_id': context.host_id, 'room_id': context.room_id})
    await asyncio.sleep(0.01)
    await client.emit(
        'room/rejoin',
        data={'room_id': context.room_id, 'user_id': context.client_id},
    )
    await asyncio.sleep(0.01)

    steps = {'1': 'DONE', '2': 'HELP', '3': 'HELP'}

    await client.emit('steps/status/to_mentor', data=steps)
    await asyncio.sleep(0.01)

    assert steps_to_mentor['user_id'] == context.client_id
    assert steps_to_mentor['steps'] == steps

    steps = {'user_id': context.client_id, 'steps': {'1': 'ACCEPTED'}}

    await host.emit('steps/status/to_client', data=steps)
    await asyncio.sleep(0.01)

    assert steps_to_client == steps['steps']


async def test_steps_table(
    host: AsyncClient,
    client: AsyncClient,
    steps_table: list,
    context: TestContext,
):
    """Test steps/table."""
    await host.emit('room/rehost', data={'user_id': context.host_id, 'room_id': context.room_id})
    await asyncio.sleep(0.01)
    await client.emit(
        'room/rejoin',
        data={'room_id': context.room_id, 'user_id': context.client_id},
    )
    await asyncio.sleep(0.01)

    await host.emit('steps/table', data={})
    await asyncio.sleep(0.01)

    assert steps_table == [
        {
            'user_id': context.client_id,
            'steps': {'1': 'ACCEPTED', '2': 'HELP', '3': 'HELP'},
        },
    ]
