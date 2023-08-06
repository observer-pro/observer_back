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

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)


def create_test_room(sid):
    """Create room for tests"""
    room = Room.get_room_by_id(1000)
    if not room:
        user = User(sid, role='host', name='Mama Zmeya')
        test_room = Room(host=user)
        test_room.add_user(user)
        # log
        sio.emit('log', data={'message': f'Test room created, id: {test_room.id}'})


@sio.event
def connect(sid, data):
    create_test_room(sid)
    sio.emit('user/connect', data='')
    # log
    sio.emit('log', data={'message': f'User {sid} connected'})


@sio.event
def disconnect(sid):
    sio.emit('user/disconnect', data='')
    # log
    sio.emit('log', data={'message': f'User {sid} disconnected'})


@sio.on('room/create')
def room_create(sid, data):
    hostname = data.get('name', None)
    user = User(sid, role='host', name=hostname)
    room = Room(host=user)
    room.add_user(user)
    user.room = room.id
    sio.emit('room/update', data=room.get_room_data(), to=sid)
    # log
    sio.emit('log', data={'message': f'User {sid} created Room id: {room.id}'})


@sio.on('room/join')
def room_join(sid, data):
    room_id = data.get('room_id', None)
    username = data.get('name', None)

    user = User.get_user_by_sid(sid)
    if user and user.room is not None:  # TODO: need I to check user in the same room already or not?
        handle_bad_request(f'User already in room (id: {user.room})')
        # log
        sio.emit('log', data={'message': f'User already in room (id: {user.room})'})
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
    sio.emit('log', data={'message': f'User {sid} has joined the Room with id: {room.id}'})


@sio.on('message/to_client')
def message_to_client(sid, data):
    send_message(sid, data, 'to_client')


@sio.on('message/to_mentor')
def message_to_mentor(sid, data):
    send_message(sid, data, 'to_mentor')


def send_message(sender_sid: str, data: dict, to: str) -> None:
    """
    Sends a message from the sender to the specified user in a room or from user to host.

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
    receiver_id = data.get('user_id', None)

    if not all((receiver_id, room_id, content)):
        # bad request "Missing some data"
        sio.emit('error', data={'message': '400 BAD REQUEST'})
        logger.error(f'Bad request occurred: Missing some data!')
        return

    room = Room.get_room_by_id(room_id)
    receiver = room.get_user_by_id(receiver_id)
    sender = User.get_user_by_sid(sender_sid)

    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    if not receiver:
        handle_bad_request(f'No such user id {receiver_id} in the room')
        return

    message = Message(sender_id=sender.id, receiver_id=receiver_id, content=content)
    # check the way of sending to save messages to user, not host
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
    sio.emit('log', data={'message': f'User {sender.id} has sent message to user: {receiver_id}'})


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
    receiver = room.get_user_by_id(receiver_id)

    if not room:
        handle_bad_request(f'No room with id: {room_id}')
        return

    if not receiver:
        handle_bad_request(f'No such user id {receiver_id} in the room')
        return

    sio.emit(f'sharing/{command}', data={}, to=receiver.sid)
    # log
    sio.emit('log', data={'message': f'Host send "{command}" to user: {receiver_id}'})


@sio.on('sharing/code_send')
def sharing_code_from_user(sid, data):
    room_id = data.get('room_id', None)
    receiver_id = data.get('user_id', None)

    room = Room.get_room_by_id(room_id)
    host = room.get_user_by_id(receiver_id)

    if not room:
        """No such Room"""
        return

    if not host:
        """Wrong host"""

    sio.emit(f'sharing/code_send', data=data, to=host.sid)
    # log
    sio.emit('log', data={'message': f'"sharing/code_send" command has been executed'})


def handle_bad_request(message: str):
    sio.emit('error', data={'message': '400 BAD REQUEST'})
    logger.error(f'Bad request occurred: {message}')


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
