import asyncio

import pytest
from socketio import AsyncClient


@pytest.mark.asyncio
async def test_room_create(host: AsyncClient, room_update: dict):
    """Test room create by host"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.1)

    user = room_update['users'][0]
    assert user['role'] == 'host'
    assert user['name'] == 'Teacher'


@pytest.mark.asyncio
async def test_room_create_join_leave(
        host: AsyncClient, client: AsyncClient, room_update: dict, room_join: dict
):
    """Test room create by host, join and leave by user"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.1)
    await client.emit('room/join', data={'room_id': room_update['id'], 'name': 'John Test'})
    await asyncio.sleep(0.1)

    assert len(room_update['users']) == 2

    response = room_update['users'][1]
    assert response['id'] == room_join['user_id']
    assert response['room'] == room_join['room_id']
    assert response['role'] == 'client'
    assert response['name'] == 'John Test'

    await client.emit('room/leave', data={'room_id': room_join['room_id']})
    await asyncio.sleep(0.1)
    assert len(room_update['users']) == 1


@pytest.mark.asyncio
async def test_signal(
        host: AsyncClient, client: AsyncClient, room_update: dict, room_join: dict
):
    """Test room create by host, join and leave by user"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.1)
    await client.emit('room/join', data={'room_id': room_update['id'], 'name': 'John Test'})
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_send_message(
        host: AsyncClient, client: AsyncClient, room_update: dict, room_join: dict, message_to_client: dict,
        message_to_mentor: dict
):
    """Test send message by host to user and vice versa"""
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.1)
    await client.emit('room/join', data={'room_id': room_update['id'], 'name': 'John Test'})
    await asyncio.sleep(0.1)

    message = {'user_id': room_join['user_id'], 'room_id': room_join['room_id'], 'content': 'Test message'}

    await host.emit('message/to_client', data=message)
    await asyncio.sleep(0.1)

    for field in ('user_id', 'room_id', 'content', 'datetime'):
        assert field in message_to_client

    message_to_client.pop('datetime')
    assert message == message_to_client  # check message to student

    message.pop('user_id')

    await client.emit('message/to_mentor', data=message)
    await asyncio.sleep(0.1)

    message_to_mentor.pop('datetime')
    message['user_id'] = room_update['host']
    assert message == message_to_mentor  # check message to mentor
