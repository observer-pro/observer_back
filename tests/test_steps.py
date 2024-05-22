import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext

NOTION_URL = 'https://it-cat.notion.site/cc1609901f894100b20b07f6b51dc37f'


async def test_steps_all(
    host: AsyncClient,
    client: AsyncClient,
    events: dict,
    context: TestContext,
):
    """Test steps/all event"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.01)
    room_update = events['room/update']
    context.room_id = room_update['id']
    context.host_id = room_update['host']
    await client.emit(
        'room/join',
        data={'room_id': context.room_id, 'name': 'John Test', 'version': '1.1'},
    )
    await asyncio.sleep(0.01)
    context.client_id = events['room/join']['user_id']

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

    assert events['steps/all'] == steps


async def test_steps_to_mentor_and_client(
    host: AsyncClient,
    client: AsyncClient,
    events: dict,
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

    steps = {'1': 'DONE', '2': 'DONE', '3': 'HELP'}
    await client.emit('steps/status/to_mentor', data=steps)
    await asyncio.sleep(0.01)

    steps_to_mentor = events['steps/status/to_mentor']

    assert steps_to_mentor['user_id'] == context.client_id
    assert steps_to_mentor['steps'] == steps

    # Check if mentor accepted task
    steps = {'user_id': context.client_id, 'steps': {'1': 'ACCEPTED'}}
    await host.emit('steps/status/to_client', data=steps)
    await asyncio.sleep(0.01)

    alerts = events['alerts']
    steps_to_client = events['steps/status/to_client']

    assert alerts['type'] == 'SUCCESS'
    assert alerts['message'] == 'Task 1 solution accepted!'
    assert steps_to_client == steps['steps']

    # Check if mentor declined task
    steps = {'user_id': context.client_id, 'steps': {'2': 'NONE'}}
    await host.emit('steps/status/to_client', data=steps)
    await asyncio.sleep(0.01)

    alerts = events['alerts']
    assert alerts['type'] == 'WARNING'
    assert alerts['message'] == 'Task 2 solution declined!'


async def test_steps_table(
    host: AsyncClient,
    client: AsyncClient,
    events: dict,
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

    assert events['steps/table'] == [
        {
            'user_id': context.client_id,
            'steps': {'1': 'ACCEPTED', '2': 'NONE', '3': 'HELP'},
        },
    ]


async def wait_for_event(events, event_name):
    while event_name not in events:
        await asyncio.sleep(0.01)


async def test_steps_import(
    host: AsyncClient,
    client: AsyncClient,
    events: dict,
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
    url = {'url': NOTION_URL}
    await host.emit('steps/import', data=url)

    await wait_for_event(events, 'steps/load')
    await wait_for_event(events, 'alerts')

    assert len(events['steps/load']) == 3
    assert events['alerts']['type'] == 'SUCCESS'
    assert events['alerts']['message'] == 'Задания были успешно загружены из Notion!'
