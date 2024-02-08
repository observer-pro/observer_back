import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext


async def test_send_messages(
    host: AsyncClient,
    client: AsyncClient,
    events: dict,
    context: TestContext,
):
    """Test send message by host to user and vice versa"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.01)
    room_update = events.get('room/update')
    await client.emit('room/join', data={'room_id': room_update['id'], 'name': 'John Test'})
    await asyncio.sleep(0.01)

    context.client_id = events['room/join']['user_id']
    context.room_id = events['room/join']['room_id']
    context.host_id = events['room/update']['host']

    message = {'user_id': context.client_id, 'room_id': context.room_id, 'content': 'Hi student'}
    await host.emit('message/to_client', data=message)
    await asyncio.sleep(0.01)

    message_to_client = events.get('message/to_client')
    message_to_client.pop('status')
    message_to_client.pop('created_at')
    assert message_to_client == {'sender': context.host_id, 'receiver': context.client_id, 'content': 'Hi student'}

    message = {'room_id': context.room_id, 'content': 'Hi teacher'}
    await client.emit('message/to_mentor', data=message)
    await asyncio.sleep(0.01)

    message_to_mentor = events.get('message/to_mentor')
    message_to_mentor.pop('status')
    message_to_mentor.pop('created_at')
    assert message_to_mentor == {'sender': context.client_id, 'receiver': context.host_id, 'content': 'Hi teacher'}


async def test_get_messages_by_user(
    host: AsyncClient,
    client: AsyncClient,
    events: dict,
    context: TestContext,
):
    """Test get messages by user"""
    await host.emit('room/rehost', data={'user_id': context.host_id, 'room_id': context.room_id})
    await asyncio.sleep(0.01)
    await client.emit(
        'room/rejoin',
        data={'room_id': context.room_id, 'user_id': context.client_id},
    )
    await asyncio.sleep(0.01)
    await host.emit('message/user', data={'user_id': context.client_id})
    await asyncio.sleep(0.01)

    user_messages = events.get('message/user')

    assert user_messages['user_id'] == context.client_id
    assert len(user_messages['messages']) == 2

    message_from_teacher, message_from_student = user_messages['messages'][0], user_messages['messages'][1]

    assert message_from_teacher['sender'] == context.host_id
    assert message_from_teacher['receiver'] == context.client_id
    assert message_from_teacher['content'] == 'Hi student'

    assert message_from_student['sender'] == context.client_id
    assert message_from_student['receiver'] == context.host_id
    assert message_from_student['content'] == 'Hi teacher'
