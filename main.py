import logging

import eventlet
import socketio

from models import Message, Room, User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('log.log')
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*')
eventlet.monkey_patch()
app = socketio.WSGIApp(sio)


def create_test_room(sid):
    """Create room for tests"""
    room = Room.get_room_by_id(1000)
    if not room:
        user = User(sid, role='host', name='Mama Zmeya')
        test_room = Room(host=user)
        test_room.add_user(user)
        # log
        emit_log(f'Test room created (id: {test_room.id})')


@sio.event
def connect(sid, data):
    create_test_room(sid)
    # log
    emit_log(f'User {sid} connected')


@sio.event
def disconnect(sid):
    # log
    emit_log(f'User {sid} disconnected')


@sio.on('room/create')
def room_create(sid, data):
    hostname = data.get('name', None)
    user = User(sid, role='host', name=hostname)
    room = Room(host=user)
    room.add_user(user)
    user.room = room.id
    sio.emit('room/update', data=room.get_room_data(), to=sid)
    # log
    emit_log(f'User {sid} created room (id: {room.id})')


@sio.on('room/join')
def room_join(sid, data):
    room_id = data.get('room_id', None)
    username = data.get('name', None)

    user = User.get_user_by_sid(sid)
    if user and user.room is not None:
        handle_bad_request(f'User already in room (id: {user.room})')
        return

    if not room_id:
        handle_bad_request(f'No room id present in data')
        return

    room = Room.get_room_by_id(room_id)
    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    user = User(sid, role='client', name=username, room_id=room_id)
    room.add_user(user)

    # Message to User
    sio.emit('room/join', data={'user_id': user.id, 'room_id': room_id}, to=sid)
    # Update data for Host
    sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
    # log
    emit_log(f'User {user.id} has joined the Room with id: {room.id}')


@sio.on('room/leave')
def room_join(sid, data):
    room_id = data.get('room_id', None)
    user = User.get_user_by_sid(sid)

    if not room_id:
        handle_bad_request(f'No room id present in data')
        return

    if not user:
        handle_bad_request(f'No user registered with sid: {sid}')
        return

    room = Room.get_room_by_id(room_id)
    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    if not room.remove_user_from_room(user.id):
        handle_bad_request(f'User is not in room (id: {user.room})')
        return

    sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
    # log
    emit_log(f'User {user.id} has left the Room with id: {room_id}')


@sio.on('room/data')
def room_data(sid, data):
    room_id = data.get('room_id', None)
    if not room_id:
        handle_bad_request(f'No room_id present in data')
        return

    room = Room.get_room_by_id(room_id)
    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    sio.emit('room/update', data=room.get_room_data(), to=sid)


@sio.on('message/to_client')
def message_to_client(sid, data):
    send_message(sid, data, 'to_client')


@sio.on('message/to_mentor')
def message_to_mentor(sid, data):
    send_message(sid, data, 'to_mentor')


def send_message(sender_sid: str, data: dict, to: str) -> None:
    """
    Sends a message from the host to the specified user in a room or from user to host.

    Parameters:
        sender_sid (str): The session ID of the sender.
        data (dict): 'user_id', 'room_id', 'content'
        to (str):
            'to_client' - from host to user
            'to_mentor' - from user to host

    Returns:
        None. The function emits the message to the recipient using Socket.IO.
    """
    room_id = data.get('room_id', None)
    content = data.get('content', None)
    room = Room.get_room_by_id(room_id)

    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    if to == 'to_client':
        receiver_id = data.get('user_id', None)
        receiver = room.get_user_by_id(receiver_id)

        if not receiver:
            handle_bad_request(f'No such user id {receiver_id} in the room')
            return
    else:
        receiver_id = room.host.id
        receiver = room.host

    if not content:
        content = ''

    sender = User.get_user_by_sid(sender_sid)
    message = Message(sender_id=sender.id, receiver_id=receiver_id, content=content)

    if to == 'to_client':
        receiver.messages.append(message)
    else:
        sender.messages.append(message)

    sio.emit(
        f'message/{to}',
        data={
            'user_id': receiver_id,
            'room_id': room_id,
            'content': content,
            'datetime': message.created_at,
        },
        to=receiver.sid,
    )
    # log
    emit_log(f'User {sender.id} has sent message to user: {receiver_id}')


@sio.on('sharing/start')
def sharing_start(sid, data):
    send_sharing_status(data, command='start')


@sio.on('sharing/end')
def sharing_end(sid, data):
    send_sharing_status(data, command='end')


def send_sharing_status(data: dict, command: str) -> None:
    room_id = data.get('room_id', None)
    receiver_id = data.get('user_id', None)
    room = Room.get_room_by_id(room_id)

    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    receiver = room.get_user_by_id(receiver_id)

    if not receiver:
        handle_bad_request(f'No such user id {receiver_id} in the room')
        return

    sio.emit(f'sharing/{command}', data={}, to=receiver.sid)
    # log
    emit_log(f"Host send '{command}' to user: {receiver_id}")


@sio.on('sharing/code_send')
def sharing_code_from_user(sid, data):
    send_sharing_code(data, command='code_send')


@sio.on('sharing/code_update')
def sharing_code_from_user(sid, data):
    send_sharing_code(data, command='code_update')


def send_sharing_code(data: dict, command: str) -> None:
    room_id = data.get('room_id', None)
    room = Room.get_room_by_id(room_id)

    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    host_sid = room.host.sid

    sio.emit(f'sharing/{command}', data=data, to=host_sid)
    # log
    emit_log(f'sharing/{command} to host with id: {room.host.id}')


@sio.on('room/rejoin')
def room_rejoin(sid, data):
    rejoin(sid, data, commmand='rejoin')


@sio.on('room/rehost')
def room_rehost(sid, data):
    rejoin(sid, data, commmand='rehost')


def rejoin(sid: str, data: dict, commmand: str) -> None:
    room_id = data.get('room_id', None)
    user_id = data.get('user_id', None)
    old_sid = data.get('old_sid', None)

    room = Room.get_room_by_id(room_id)
    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    user = room.get_user_by_id(user_id)
    if not user:
        handle_bad_request(f'No such user with id {user_id}!')
        return

    if not user.sid == old_sid:
        handle_bad_request(f'Wrong old_sid for user id: {user_id}!')
        return

    user.sid = sid  # Save new socket id to user

    if commmand == 'rejoin':  # Student rejoin
        sio.emit('room/join', data={'user_id': user.id, 'room_id': room_id}, to=sid)
        # log
        emit_log(f'Student {user.name} with id {user_id} reconnected!')
    else:  # Teacher rejoin
        sio.emit('room/update', data=room.get_room_data(), to=sid)
        for user in room.users:
            if user != room.host:
                sio.emit('message', {'message': 'The teacher is back!'}, to=user.sid)
        # log
        emit_log(f'Host {user.name} with id {user_id} reconnected!')


@sio.on('room/close')
def room_close(sid, data):
    room_id = data.get('room_id', None)

    room = Room.get_room_by_id(room_id)
    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    for user in room.users:
        if user != room.host:
            user.room = None
            sio.emit('room/closed', {'message': 'Room closed!'}, to=user.sid)

    eventlet.sleep(2)
    Room.delete_room(room_id)


def emit_log(message):
    sio.emit('log', data={'message': message})


def handle_bad_request(message: str):
    sio.emit('error', data={'message': f'400 BAD REQUEST. {message}'})
    logger.error(f'Bad request occurred: {message}')


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
