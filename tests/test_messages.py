import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext


async def test_send_messages(
    host: AsyncClient,
    client: AsyncClient,
    room_update: dict,
    room_join: dict,
    message_to_client: dict,
    message_to_mentor: dict,
    context: TestContext,
):
    """Test send message by host to user and vice versa"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.01)
    await client.emit('room/join', data={'room_id': room_update['id'], 'name': 'John Test'})
    await asyncio.sleep(0.01)

    context.client_id = room_join['user_id']
    context.room_id = room_join['room_id']
    context.host_id = room_update['host']

    message = {'user_id': context.client_id, 'room_id': context.room_id, 'content': 'Hi student'}

    await host.emit('message/to_client', data=message)
    await asyncio.sleep(0.01)

    for field in ('user_id', 'room_id', 'content', 'datetime'):
        assert field in message_to_client

    message_to_client.pop('datetime')
    assert message == message_to_client  # check message to student

    message = {'user_id': context.client_id, 'room_id': context.room_id, 'content': 'Hi teacher'}

    await client.emit('message/to_mentor', data=message)
    await asyncio.sleep(0.01)

    message_to_mentor.pop('datetime')
    assert message == message_to_mentor  # check message to mentor


async def test_get_messages_by_user(
    host: AsyncClient,
    client: AsyncClient,
    get_user_messages: dict,
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

    assert get_user_messages['user_id'] == context.client_id
    assert len(get_user_messages['messages']) == 2

    message_from_teacher, message_from_student = get_user_messages['messages'][0], get_user_messages['messages'][1]

    assert message_from_teacher['sender'] == context.host_id
    assert message_from_teacher['receiver'] == context.client_id
    assert message_from_teacher['content'] == 'Hi student'

    assert message_from_student['sender'] == context.client_id
    assert message_from_student['receiver'] == context.host_id
    assert message_from_student['content'] == 'Hi teacher'
