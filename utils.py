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
        if key in ('content', 'files_to_ignore'):
            return True
        if key == 'accepted' and not isinstance(data[key], bool):
            handle_bad_request(sio, f'{key} should be a boolean')
            return False
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
    """
    Send sharing status to a user in a specific room.
    Args:
        sio (socketio.Server): The Socket.IO server instance.
        data (dict): The data containing the room ID and user ID.
        command (str): The command to send (start or end).
    Returns:
        None
    """
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
    emit_log(sio, f"Host send '{command}' to the user: {receiver_id}")


def send_sharing_code(sio: socketio.Server, sid: str, data: dict, command: str) -> None:
    """
    Send sharing code to the host in the specified room.
    Args:
        sio (socketio.Server): The Socket.IO server instance.
        sid (str): The session ID of the user.
        data (dict): The data to be sent.
        command (str): The command to be sent (code_send or code_update).
    Returns:
        None
    """
    if not validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)
    user = User.get_user_by_sid(sid)
    data.update({'user_id': user.id})

    sio.emit(f'sharing/{command}', data=data, to=room.host.sid)
    # log
    emit_log(sio, f'sharing/{command} to host with id: {room.host.id}')


def send_exercise(sio: socketio.Server, data: dict, sid: str) -> None:
    """
    Send exercise to all students in the same room as the host with the given sid
    Args:
        sio (socketio.Server): The socketio server instance.
        data (dict): The data containing the exercise content.
        sid (str): The session ID of the user.
    Returns:
        None
    """
    if not validate_data(sio, data, 'content'):
        return

    content = data.get('content', '')
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    room.exercise = content  # Save exercise

    for student in room.users:
        if student.role == 'client':
            sio.emit('exercise', data={'content': content}, to=student.sid)
    # log
    emit_log(sio, f'The exercise was sent to all students in the room {room_id}!')


def send_exercise_feedback(sio: socketio.Server, data: dict) -> None:
    """
    Sends exercise feedback to a user via socketio.
    Args:
        sio (socketio.Server): The socketio server instance.
        data (dict): The data containing the user's room_id, user_id, and accept status (true or false).
    Returns:
        None
    """
    if not validate_data(sio, data, 'room_id', 'user_id', 'accepted'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    user_id = data.get('user_id', None)
    user = room.get_user_by_id(user_id)
    if not user:
        handle_bad_request(sio, f'No such user with id {user_id}!')
        return

    accepted = data.get('accepted')
    sio.emit('exercise/feedback', data={'accepted': accepted}, to=user.sid)
    # log
    emit_log(sio, f'Feedback (accepted: {accepted}) was sent to the user with id: {user.id}')


def send_exercise_reset(sio: socketio.Server, sid: str) -> None:
    """
    Sends a 'exercise/reset' event to all students in the same room as the host with the given sid
    Args:
        sio (socketio.Server): The socket.io server instance.
        sid (str): The session ID of the user.
    Returns:
        None
    """
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    for student in room.users:
        if student.role == 'client':
            sio.emit('exercise/reset', data={}, to=student.sid)
    # log
    emit_log(sio, f'The exercise/reset was sent to all students in the room {room_id}!')


def send_settings(sio: socketio.Server, data: dict, sid: str) -> None:
    """
    Sends settings to all students in the room.
    Args:
        sio (socketio.Server): The socketio server instance.
        data (dict): The data containing the settings.
        sid (str): The session ID of the user.
    """
    if not validate_data(sio, data, 'files_to_ignore'):
        return

    files_to_ignore = data.get('files_to_ignore', '')
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    room.settings = files_to_ignore  # Save settings

    for student in room.users:
        if student.role == 'client':
            sio.emit('settings', data={'files_to_ignore': files_to_ignore}, to=student.sid)
    # log
    emit_log(sio, f'The settings were sent to all students in the room {room_id}!')


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
