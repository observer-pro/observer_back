import time


def test_room_create(host, room_update):
    """Test room create by host"""
    host.emit('room/create', data={'name': 'Teacher'})
    time.sleep(0.1)

    user = room_update['users'][0]
    assert user['role'] == 'host'
    assert user['name'] == 'Teacher'


def test_room_create_join_leave(client, host, room_update, room_join):
    """Test room create by host, join and leave by user"""
    host.emit('room/create', data={'name': 'Teacher'})
    time.sleep(0.1)

    client.emit('room/join', data={'room_id': room_update['id'], 'name': 'Test name'})
    time.sleep(0.1)

    response = room_update['users'][1]

    assert len(room_update['users']) == 2
    assert response['id'] == room_join['user_id']
    assert response['room'] == room_join['room_id']
    assert response['role'] == 'client'
    assert response['name'] == 'Test name'

    client.emit('room/leave', data={'room_id': room_join['room_id']})
    time.sleep(0.1)

    assert len(room_update['users']) == 1


def test_send_message(client, host, room_update, room_join, message_to_client, message_to_mentor):
    """Test send message by host to user and vice versa"""
    host.emit('room/create', data={'name': 'Teacher'})
    time.sleep(0.1)

    client.emit('room/join', data={'room_id': room_update['id'], 'name': 'Test name'})
    time.sleep(0.1)

    message = {'user_id': room_join['user_id'], 'room_id': room_join['room_id'], 'content': 'Test message'}

    host.emit('message/to_client', data=message)
    time.sleep(0.1)

    for field in ('user_id', 'room_id', 'content', 'datetime'):
        assert field in message_to_client

    message_to_client.pop('datetime')

    assert message == message_to_client  # check message to student

    message.pop('user_id')
    client.emit('message/to_mentor', data=message)
    time.sleep(0.1)

    message_to_mentor.pop('datetime')
    message['user_id'] = room_update['host']

    assert message == message_to_mentor  # check message to mentor
