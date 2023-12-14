from socketio import AsyncServer

from src.classes.external_api import ExternalAPIClient
from src.models import Room, User
from src.scraper.notion_scraper import get_exercises_from_notion

from .utils import AllertsEnum, alerts, deprecated, emit_log, handle_bad_request, validate_data


# deprecated from v1.1.0
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


# deprecated from v1.1.0
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
    await emit_log(sio, f'Feedback (accepted: {accepted}) was sent to the user with id: {user.uid}')
    await deprecated(sio, 'exercise/feedback')


# deprecated from the v1.1.0
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
    await deprecated(sio, 'exercise/reset')


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
        item for item in data if 'content' in item and item['content'] is not None and item['content'].strip() != ''
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


async def send_statuses_from_host(sio: AsyncServer, sid: str, data: dict[str, int | dict[str, str]]) -> None:
    if not await validate_data(sio, data, 'user_id'):
        return

    steps: dict = data.get('steps')
    host = User.get_user_by_sid(sid)
    room_id = host.room
    room = Room.get_room_by_id(room_id)
    user_id = data.get('user_id')
    user = room.get_user_by_id(user_id)
    if not user:
        await handle_bad_request(sio, f'No such user with id {user_id} in the Room {room_id}!')
        return
    if not user.steps:
        user.steps = steps
    else:
        for step, status in steps.items():
            if step in user.steps:
                user.steps[step] = status

    await sio.emit('steps/status/to_client', data=data, to=user.sid)
    # log
    await emit_log(sio, f'The statuses were sent to the client (User id: {user.uid}) in the Room {room_id}!')


async def send_statuses_from_student(sio: AsyncServer, sid: str, data: dict[str, str]) -> None:
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

    await sio.emit('steps/status/to_mentor', data={'user_id': user.uid, 'steps': data}, to=room.host.sid)
    # log
    await emit_log(
        sio, f'The steps were sent from the student (id: {user.uid}) to the host of the room {room_id}!',
    )


async def send_table(sio: AsyncServer, sid: str) -> None:
    """
    Send the steps of all students to the host.
    Args:
        sio (AsyncServer): The SocketIO server.
        sid (str): The session ID of the host.
    Returns:
        None
    """
    host = User.get_user_by_sid(sid)
    room_id = host.room
    room = Room.get_room_by_id(room_id)
    data = [
        {'user_id': user.uid, 'steps': user.steps}
        for user in room.users if user.steps
    ]

    await sio.emit('steps/table', data=data, to=sid)
    # log
    await emit_log(sio, f'The steps/table was sent to host {host.uid}!')


async def import_steps_from_notion(sio: AsyncServer, sid: str, data: dict[str, str]) -> None:
    """
    Get Notion url from the host and parse the steps from Notion.
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict[str, str]): The data containing the Notion url.
    """
    if not await validate_data(sio, data):
        return

    url = data.get('url')
    result = await get_exercises_from_notion(url)

    if isinstance(result, list):
        room_id = User.get_user_by_sid(sid).room
        room = Room.get_room_by_id(room_id)
        steps = [
            {
                'name': str(count),
                'content': content,
                'language': 'html',
                'type': 'exercise',
            }
            for count, content in enumerate(result, 1)
            if content != ''
        ]

        if len(steps) == 0:
            await alerts(sio, sid, 'Похоже в вашем Notion нет заданий!', AllertsEnum.ERROR)
            await handle_bad_request(sio, message='Notion has no steps!')
            return

        room.steps = steps

        await sio.emit('steps/load', data=steps, to=sid)
        await alerts(sio, sid, 'Задания были успешно загружены из Notion!', AllertsEnum.SUCCESS)
        # log
        await emit_log(sio, 'The steps were loaded from Notion and sent to the host!')
    else:
        await alerts(
            sio, sid, result.get('message', 'Something went wrong with loading steps from Notion'), AllertsEnum.ERROR,
        )
        await handle_bad_request(sio, message=result.get('message'))


async def send_solution_from_ai(sio: AsyncServer, sid: str, data: dict[str, str]) -> None:
    """
    Sends the solution from the AI to the student with the given sid.
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the solution.
    """
    if not await validate_data(sio, data):
        return
    content = data.get('content')
    code = data.get('code')
    if not content or not code:
        await handle_bad_request(sio, 'Task content and code are required!')
        return

    await emit_log(sio, 'solution/ai data sent to AI')

    client = ExternalAPIClient()
    ai_response: dict = await client.get_solution({'content': content, 'code': code})

    if not ai_response['status']:
        await handle_bad_request(sio, ai_response['content'])
        return

    await sio.emit('solution/ai', data={'content': ai_response['content']}, to=sid)
    # log
    await emit_log(sio, f'The AI solution was sent to the student with id: {sid}!')
