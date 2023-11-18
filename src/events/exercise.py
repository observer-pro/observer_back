from socketio import AsyncServer

from src.classes.openai import AIClient
from src.models import Room, User

from .utils import deprecated, emit_log, handle_bad_request, validate_data


# deprecated from the v1.1.0
async def send_exercise(sio: AsyncServer, sid: str, data: dict) -> None:
    """
    Sends an exercise to all students in the same room as the host with the given sid
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the exercise content.
    """
    if not await validate_data(sio, data):
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
    await deprecated(sio, 'exercise', 'steps/all')


async def send_exercise_feedback(sio: AsyncServer, data: dict) -> None:
    """
    Sends an exercise feedback to a user via socketio.
    Args:
        sio (AsyncServer): The socketio server instance.
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


async def send_exercise_reset(sio: AsyncServer, sid: str) -> None:
    """
    Sends an 'exercise/reset' event to all students in the same room as the host with the given sid
    Args:
        sio (AsyncServer): The socket.io server instance.
        sid (str): The session ID of the user.
    """
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    for student in room.users:
        if student.role == 'client':
            await sio.emit('exercise/reset', data={}, to=student.sid)
    # log
    await emit_log(sio, f'The exercise/reset was sent to all students in the room {room_id}!')


async def send_steps_from_host(sio: AsyncServer, sid: str, data: list[dict[str, str]]) -> None:
    """
    Sends steps from the host to all students in the same room as the host with the given sid
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (list[dict]): The data containing the steps.
    """
    if not isinstance(data, list):
        await handle_bad_request(sio, 'Data should be a JSON array')
        return

    cleaned_data = [
        item for item in data if "content" in item and item["content"] is not None and item["content"].strip() != ""
    ]

    host = User.get_user_by_sid(sid)
    room_id = host.room
    room = Room.get_room_by_id(room_id)

    room.steps = cleaned_data

    for student in room.users:
        if student.role == 'client':
            await sio.emit('steps/all', data=cleaned_data, to=student.sid)
    # log
    await emit_log(sio, f'The steps were sent to all students in the room {room_id}!')


async def send_steps_from_student(sio: AsyncServer, sid: str, data: dict[str, str]) -> None:
    """
    Sends steps from the student to the host of the room.
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the statuses of the tasks.
    """
    if not await validate_data(sio, data):
        return

    user = User.get_user_by_sid(sid)
    room_id = user.room
    room = Room.get_room_by_id(room_id)

    user.steps = data

    await sio.emit('steps/status', data={'user_id': user.id, 'steps': data}, to=room.host.sid)
    # log
    await emit_log(
        sio, f'The steps were sent from the student (id: {user.id}) to the host of the room {room_id}!'
    )


async def send_solution_from_ai(sio: AsyncServer, sid: str, data: dict[str, str]) -> None:
    """
    Sends the solution from the AI to the student with the given sid.
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the question and code.
    """
    if not await validate_data(sio, data):
        return
    task = data.get('content')
    code = data.get('code')
    if not task or not code:
        await handle_bad_request(sio, 'Task content and code are required!')
        return

    await emit_log(sio, 'solution/ai data sent to AI')

    ai_client = AIClient()
    ai_response = await ai_client.get_explanation(task, code)

    await sio.emit('solution/ai', data={'content': ai_response}, to=sid)
    # log
    await emit_log(sio, f'The solution was sent from the AI to the student with id: {sid}!')
