import logging

import socketio

from models import Message, Room, StatusEnum, User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('log.log')
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def create_test_room(sio: socketio.Server, sid) -> None:
    """Create room for tests"""
    room = Room.get_room_by_id(1000)
    if not room:
        user = User(sid, role='host', name='Mama Zmeya')
        test_room = Room(host=user)
        test_room.add_user(user)
        # log
        emit_log(sio, f'Test room created (id: {test_room.id})')


def validate_data(sio: socketio.Server, data, *keys) -> bool:
    """
    Validate incoming data

    Args:
        sio: SocketIO server
        data: JSON object
        *keys: list of keys

    Returns:
        True if data is valid
    """
    if not isinstance(data, dict):
        handle_bad_request(sio, 'Data should be a JSON object')
        return False

    for key in keys:
        if key not in data:
            handle_bad_request(sio, f'No [{key}] present in data')
            return False
        if key == 'content':
            return True
        if not isinstance(data[key], int):
            handle_bad_request(sio, f'{key} should be an integer')
            return False
        if key == 'room_id' and not Room.get_room_by_id(data[key]):
            handle_bad_request(sio, f'No room with id: {data[key]}')
            return False
    return True


def send_message(sio: socketio.Server, sender_sid: str, data: dict, to: str) -> None:
    """
    Sends a message from the host to the specified user in a room or from user to host.

    Parameters:
        sio: SocketIO server
        sender_sid (str): The session ID of the sender.
        data (dict): 'user_id', 'room_id', 'content'
        to (str):
            'to_client' - from host to user
            'to_mentor' - from user to host

    Returns:
        None. The function emits the message to the recipient using Socket.IO.
    """
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)
    content = data.get('content', None)
    if not content:
        content = ''

    if to == 'to_client':
        receiver_id = data.get('user_id', None)
        receiver = room.get_user_by_id(receiver_id)

        if not receiver:
            handle_bad_request(sio, f'No such user id {receiver_id} in the room')
            return
    else:
        receiver_id = room.host.id
        receiver = room.host

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
    emit_log(sio, f'User {sender.id} has sent message to user: {receiver_id}')


def send_sharing_status(sio: socketio.Server, data: dict, command: str) -> None:
    if not validate_data(sio, data, 'room_id', 'user_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    receiver_id = data.get('user_id')
    receiver = room.get_user_by_id(receiver_id)
    if not receiver:
        handle_bad_request(sio, f'No such user id {receiver_id} in the room')
        return

    sio.emit(f'sharing/{command}', data={}, to=receiver.sid)
    # log
    emit_log(sio, f"Host send '{command}' to user: {receiver_id}")


def send_sharing_code(sio: socketio.Server, data: dict, command: str) -> None:
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    sio.emit(f'sharing/{command}', data=data, to=room.host.sid)
    # log
    emit_log(sio, f'sharing/{command} to host with id: {room.host.id}')


def send_exercise(sio: socketio.Server, data: dict, sid: str) -> None:
    if not validate_data(sio, data, 'content'):
        return

    content = data.get('content', '')
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    for student in room.users:
        if student.role == 'client':
            sio.emit('exercise', data={'content': content}, to=student.sid)
    # log
    emit_log(sio, 'The task has been sent out to the students!')


def rejoin(sio: socketio.Server, sid: str, data: dict, commmand: str) -> None:
    if not validate_data(sio, data, 'room_id', 'user_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    user_id = data.get('user_id', None)
    user = room.get_user_by_id(user_id)
    if not user:
        handle_bad_request(sio, f'No such user with id {user_id}!')
        return

    user.set_new_sid(sid)  # Save new socket id to user
    user.status = StatusEnum.ONLINE  # Update user status

    if commmand == 'rejoin':  # Student rejoin
        # 'room/join' to reconnected student
        sio.emit('room/join', data={'user_id': user.id, 'room_id': room_id}, to=sid)
        # Update data for teacher
        sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
        # log
        emit_log(sio, f'Student {user.name} with id {user_id} reconnected!')
    else:  # Teacher rehost
        # Messages to students
        for student in room.users:
            if student.role == 'client':
                sio.emit('message', {'message': 'STATUS: The teacher is back!'}, to=student.sid)
        # log
        emit_log(sio, f'Host {user.name} with id {user_id} reconnected!')

    # Update data for teacher
    sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)


def emit_log(sio: socketio.Server, message: str) -> None:
    sio.emit('log', data={'message': message})


def handle_bad_request(sio: socketio.Server, message: str) -> None:
    sio.emit('error', data={'message': f'400 BAD REQUEST. {message}'})
    logger.error(f'Bad request occurred: {message}')
