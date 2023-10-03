import random

import eventlet
import socketio

from models import Room, SignalEnum, StatusEnum, User
from utils import (
    create_test_room,
    emit_log,
    handle_bad_request,
    rejoin,
    send_exercise,
    send_message,
    send_sharing_code,
    send_sharing_status,
    validate_data,
)

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*')
eventlet.monkey_patch()
app = socketio.WSGIApp(sio)


@sio.event
def connect(sid, data):
    create_test_room(sio, sid)
    # log
    emit_log(sio, f'User {sid} connected')


@sio.event
def disconnect(sid):
    user = User.get_user_by_sid(sid)
    if user and user.room:
        user.status = StatusEnum.OFFLINE
        room = Room.get_room_by_id(user.room)

        if user.role == 'host':  # teacher disconnected
            for student in room.users:
                if student.role == 'client':
                    sio.emit('message', {'message': 'STATUS: The teacher is offline!'}, to=student.sid)
            # log
            emit_log(sio, f'Teacher disconnected (host id: {user.id}, room id: {room.id})')
        else:  # student disconnected
            sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
            # log
            emit_log(sio, f'Student disconnected (id: {user.id}, room id: {room.id})')


@sio.on('room/create')
def room_create(sid, data):
    hostname = data.get('name', None)
    user = User(sid, role='host', name=hostname)
    room = Room(host=user)
    room.add_user(user)
    user.room = room.id
    sio.emit('room/update', data=room.get_room_data(), to=sid)
    # log
    emit_log(sio, f'User {sid} created room (id: {room.id})')


@sio.on('room/join')
def room_join(sid, data):
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    username = data.get('name', None)
    if not username:
        username = 'Guest ' + str(random.randint(1, 10000))

    user = User.get_user_by_sid(sid)
    if user and user.room is not None:
        handle_bad_request(sio, f'User already in room (id: {user.room})')
        return

    user = User(sid, role='client', name=username, room_id=room_id)
    room.add_user(user)

    # Message to student
    sio.emit('room/join', data={'user_id': user.id, 'room_id': room_id}, to=sid)
    # If exercise exists, send it to student
    if room.exercise:
        sio.emit('exercise', data={'content': room.exercise}, to=sid)
        # log
        emit_log(sio, f'The exercise was sent to the student (id: {user.id})!')

    # Update data for teacher
    sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
    # log
    emit_log(sio, f'User {user.id} has joined the Room with id: {room_id}')


@sio.on('room/leave')
def room_leave(sid, data):
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)
    user = User.get_user_by_sid(sid)

    if not user:
        handle_bad_request(sio, f'No user registered with sid: {sid}')
        return

    if not room.remove_user_from_room(user.id):
        handle_bad_request(sio, f'User is not in room (id: {user.room})')
        return

    sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
    # log
    emit_log(sio, f'User {user.id} has left the Room with id: {room_id}')


@sio.on('room/data')
def room_data(sid, data):
    """Just for testing"""
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id', None)
    room = Room.get_room_by_id(room_id)

    sio.emit('room/update', data=room.get_room_data(), to=sid)


@sio.on('signal')
def signal(sid, data):
    if not validate_data(sio, data, 'user_id'):
        return

    signal_value = data.get('value', None)
    if not signal_value:
        handle_bad_request(sio, 'No signal received')
        return

    try:
        SignalEnum(signal_value)
    except ValueError:
        handle_bad_request(sio, f'Invalid signal: {signal_value}')
        return

    user = User.get_user_by_sid(sid)
    user.signal = signal_value
    room = Room.get_room_by_id(user.room)

    sio.emit('signal', data=data, to=room.host.sid)
    # log
    emit_log(sio, f'The user {user.id} sent a [{signal_value}] signal to host with id {room.host.id}.')


@sio.on('message/to_client')
def message_to_client(sid, data):
    send_message(sio, sid, data, 'to_client')


@sio.on('message/to_mentor')
def message_to_mentor(sid, data):
    send_message(sio, sid, data, 'to_mentor')


@sio.on('sharing/start')
def sharing_start(sid, data):
    send_sharing_status(sio, data, command='start')


@sio.on('sharing/end')
def sharing_end(sid, data):
    send_sharing_status(sio, data, command='end')


@sio.on('sharing/code_send')
def sharing_code_send(sid, data):
    send_sharing_code(sio, data, command='code_send')


@sio.on('sharing/code_update')
def sharing_code_update(sid, data):
    send_sharing_code(sio, data, command='code_update')


@sio.on('exercise')
def sharing_exercise(sid, data):
    send_exercise(sio, data, sid)


@sio.on('room/rejoin')
def room_rejoin(sid, data):
    rejoin(sio, sid, data, commmand='rejoin')


@sio.on('room/rehost')
def room_rehost(sid, data):
    rejoin(sio, sid, data, commmand='rehost')


@sio.on('room/close')
def room_close(sid, data):
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    for student in room.users:
        if student.role == 'client':
            sio.emit('room/closed', {'message': 'Room closed!'}, to=student.sid)

    eventlet.sleep(2)
    Room.delete_room(room_id)  # Delete all users in the room and room itself
    # log
    emit_log(sio, f'Room with id: {room_id} has been closed!')


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
