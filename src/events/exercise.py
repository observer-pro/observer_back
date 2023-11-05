import socketio

from src.models import Room, User

from .utils import emit_log, handle_bad_request, validate_data


async def send_exercise(sio: socketio.AsyncServer, data: dict, sid: str) -> None:
    """
    Send exercise to all students in the same room as the host with the given sid
    Args:
        sio (socketio.AsyncServer): The socketio server instance.
        data (dict): The data containing the exercise content.
        sid (str): The session ID of the user.
    """
    if not await validate_data(sio, data, 'content'):
        return

    content = data.get('content', '')
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    room.exercise = content  # Save exercise

    for student in room.users:
        if student.role == 'client':
            await sio.emit('exercise', data={'content': content}, to=student.sid)
    # log
    await emit_log(sio, f'The exercise was sent to all students in the room {room_id}!')


async def send_exercise_feedback(sio: socketio.AsyncServer, data: dict) -> None:
    """
    Sends exercise feedback to a user via socketio.
    Args:
        sio (socketio.AsyncServer): The socketio server instance.
        data (dict): The data containing the user's room_id, user_id, and accept status (true or false).
    """
    if not await validate_data(sio, data, 'room_id', 'user_id', 'accepted'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    user_id = data.get('user_id', None)
    user = room.get_user_by_id(user_id)
    if not user:
        await handle_bad_request(sio, f'No such user with id {user_id}!')
        return

    accepted = data.get('accepted')
    await sio.emit('exercise/feedback', data={'accepted': accepted}, to=user.sid)
    # log
    await emit_log(sio, f'Feedback (accepted: {accepted}) was sent to the user with id: {user.id}')


async def send_exercise_reset(sio: socketio.AsyncServer, sid: str) -> None:
    """
    Sends a 'exercise/reset' event to all students in the same room as the host with the given sid
    Args:
        sio (socketio.AsyncServer): The socket.io server instance.
        sid (str): The session ID of the user.
    """
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    for student in room.users:
        if student.role == 'client':
            await sio.emit('exercise/reset', data={}, to=student.sid)
    # log
    await emit_log(sio, f'The exercise/reset was sent to all students in the room {room_id}!')
