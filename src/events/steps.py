from src.components import logger, sio
from src.exceptions import RoomNotFoundError, UserNotFoundError
from src.managers import room_manager, user_manager
from src.models import SignalEnum
from src.scraper.notion_scraper import get_exercises_from_notion

from .utils import AlertsEnum, Utils

utils = Utils(sio, logger)


def register_steps_events() -> None:
    """Register steps events"""
    sio.on('steps/all', steps_all)
    sio.on('steps/status/to_client', steps_status_to_client)
    sio.on('steps/status/to_mentor', steps_status_to_mentor)
    sio.on('steps/table', steps_table)
    sio.on('steps/import', steps_import)

    sio.on('exercise', exercise)  # deprecated from v1.1.0
    sio.on('exercise/feedback', exercise_feedback)  # deprecated from v1.1.0
    sio.on('exercise/reset', exercise_reset)  # deprecated from v1.1.0
    sio.on('signal', signal)  # deprecated from v1.1.0


async def steps_all(sid: str, data: list[dict[str, str]]) -> None:
    """
    Sends tasks from the host to all students in the same room as the host with the given sid
    Args:
        sid (str): The session ID of the user.
        data (list[dict]): The data containing the steps.
    """
    event = 'steps/all'

    if not isinstance(data, list):
        await utils.handle_bad_request(f'Event: {event}. Data should be a JSON array')
        return

    cleaned_data = [
        item
        for item in data
        if 'content' in item
        and item['content'] is not None
        and item['content'].strip() != ''
        and (item['name'] in {str(i) for i in range(1, 17)} or item['name'] == 'theory')
    ]

    try:
        host = user_manager.get_user_by_sid(sid)
        room_id = host.room
        room = room_manager.get_room_by_id(room_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Host with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Room not found!')
        return

    room.steps = cleaned_data
    await sio.emit(event, data=cleaned_data, room=room_id)
    logger.debug(f'Tasks were sent to all students in the room {room_id}!', extra={'sid': sid})


async def steps_status_to_client(sid: str, data: dict[str, int | dict[str, str]]) -> None:
    """
    Sends statuses from the host to the client with user_id
    Args:
        sid (str): The session ID of the user.
        data (dict[str, int | dict[str, str]]): The data containing user_id and the steps.
    """
    event = 'steps/status/to_client'

    if not await utils.validate_data(data, 'user_id'):
        return

    steps: dict = data.get('steps')
    try:
        host = user_manager.get_user_by_sid(sid)
        room_id = host.room
        room = room_manager.get_room_by_id(room_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Host with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Room not found!')
        return

    user_id = data.get('user_id')
    try:
        user = room.get_user_by_id(user_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. User {user_id} in room {room_id} not found!')
        return

    if not user.steps:
        user.steps = steps
    else:
        for step, status in steps.items():
            if step in user.steps:
                if status == 'NONE' and user.steps[step] == 'DONE':
                    await utils.alerts(
                        user.sid,
                        f'Task {step} solution declined!',
                        AlertsEnum.WARNING,
                    )
                elif status == 'ACCEPTED' and user.steps[step] != status:
                    await utils.alerts(
                        user.sid,
                        f'Task {step} solution accepted!',
                        AlertsEnum.SUCCESS,
                    )
                user.steps[step] = status

    await sio.emit(event, data=steps, to=user.sid)
    logger.debug(f'Statuses were sent to user {user.uid} in the room {room_id}!', extra={'sid': sid})


async def steps_status_to_mentor(sid: str, data: dict[str, str]) -> None:
    """
    Sends statuses from the student to the host of the room.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing the statuses of the tasks.
    """
    event = 'steps/status/to_mentor'

    if not await utils.validate_data(data):
        return

    try:
        user = user_manager.get_user_by_sid(sid)
        room_id = user.room
        room = room_manager.get_room_by_id(room_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. User with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Room not found!')
        return

    user.steps = data

    await sio.emit(event, data={'user_id': user.uid, 'steps': data}, to=room.host.sid)
    logger.debug(f'Statuses were sent from user {user.uid} to the host of the room {room_id}!', extra={'sid': sid})


async def steps_table(sid: str, data) -> None:
    """
    Send the steps of all students to the host.
    Args:
        sid (str): The session ID of the host.
        data (dict): not using
    """
    event = 'steps/table'

    try:
        host = user_manager.get_user_by_sid(sid)
        room_id = host.room
        room = room_manager.get_room_by_id(room_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Host with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Room not found!')
        return

    table = [{'user_id': user.uid, 'steps': user.steps} for user in room.users.values() if user.steps]
    await sio.emit(event, data=table, to=sid)
    logger.debug(f'Steps table was sent to host {host.uid}!', extra={'sid': sid})


async def steps_import(sid: str, data: dict[str, str]) -> None:
    """
    Get Notion url from the host and parse the steps from Notion.
    Args:
        sid (str): The session ID of the user.
        data (dict[str, str]): The data containing the Notion url.
    """
    event = 'steps/import'

    if not await utils.validate_data(data):
        return

    url = data.get('url')
    result = await get_exercises_from_notion(url)

    if isinstance(result, list):
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
            await utils.alerts(sid, 'Похоже в вашем Notion нет заданий!', AlertsEnum.ERROR)
            await utils.handle_bad_request(f'Event: {event}. Notion has no steps!')
            return

        try:
            host = user_manager.get_user_by_sid(sid)
            room_id = host.room
            room = room_manager.get_room_by_id(room_id)
            room.steps = steps
            await sio.emit('steps/load', data=steps, to=sid)
            await utils.alerts(sid, 'Задания были успешно загружены из Notion!', AlertsEnum.SUCCESS)
        except UserNotFoundError:
            await utils.handle_bad_request(f'Event: {event}. Host with sid {sid} not found!')
            return
        except RoomNotFoundError:
            await utils.handle_bad_request(f'Event: {event}. Room not found!')
            return
        logger.debug('The steps were loaded from Notion and sent to the host!', extra={'sid': sid})
    else:
        await utils.alerts(
            sid,
            result.get('message', 'Something went wrong with loading steps from Notion'),
            AlertsEnum.ERROR,
        )
        await utils.handle_bad_request(result.get('message'))


async def exercise(sid: str, data: dict) -> None:
    """
    Deprecated from v1.1.0

    Sends an exercise to all students in the same room as the host with the given sid
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing the exercise content.
    """
    if not await utils.validate_data(data):
        return

    content = data.get('content', '')
    try:
        host = user_manager.get_user_by_sid(sid)
        room_id = host.room
        room = room_manager.get_room_by_id(room_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Host with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request('Room not found!')
        return

    room.exercise = content  # Save exercise
    await sio.emit('exercise', {'content': content}, room=room_id)
    await utils.deprecated('exercise', 'steps/all')
    logger.debug(f'The exercise was sent to all students in the room {room_id}!', extra={'sid': sid})


async def exercise_feedback(sid: str, data: dict) -> None:
    """
    Deprecated from v1.1.0

    Sends an exercise feedback to the user.
    Args:
        sid (str): not using
        data (dict): The data containing the user's room_id, user_id, and accept status (true or false).
    """
    if not await utils.validate_data(data, 'room_id', 'user_id', 'accepted'):
        return

    room_id = data.get('room_id')
    user_id = data.get('user_id')
    try:
        room = room_manager.get_room_by_id(room_id)
        user = room.get_user_by_id(user_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'User {user_id} in room {room_id} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Room {room_id} not found!')
        return

    accepted = data.get('accepted')
    await sio.emit('exercise/feedback', data={'accepted': accepted}, to=user.sid)
    await utils.deprecated('exercise/feedback')
    logger.debug(f'Feedback "{accepted}" was sent to the user with id: {user.uid}', extra={'sid': sid})


async def exercise_reset(sid: str, data: dict) -> None:
    """
    Deprecated from v1.1.0

    Sends an 'exercise/reset' event to all students in the same room as the host with the given sid
    Args:
        sid (str): The session ID of the user.
        data (dict): not using
    """
    try:
        host = user_manager.get_user_by_sid(sid)
        room_id = host.room
    except UserNotFoundError:
        await utils.handle_bad_request(f'Host with sid {sid} not found!')
        return

    await sio.emit('exercise/reset', data={}, room=room_id)
    await utils.deprecated('exercise/reset')
    logger.debug(f'The exercise/reset was sent to all students in the room {room_id}!', extra={'sid': sid})


async def signal(sid: str, data: dict) -> None:
    """
    Deprecated from v1.1.0

    Send signal to the teacher.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing the user ID and one of SignalEnum values.
    """
    if not await utils.validate_data(data, 'user_id'):
        return

    signal_value = data.get('value')
    if not signal_value:
        await utils.handle_bad_request('No signal received')
        return

    try:
        SignalEnum(signal_value)
    except ValueError:
        await utils.handle_bad_request(f'Invalid signal: {signal_value}')
        return

    try:
        user = user_manager.get_user_by_sid(sid)
        user.signal = signal_value
        room = room_manager.get_room_by_id(user.room)
    except UserNotFoundError:
        await utils.handle_bad_request(f'User with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request('Room not found!')
        return

    await sio.emit('signal', data=data, to=room.host.sid)
    await utils.deprecated('signal')
    logger.debug(f'User {user.uid} sent a {signal_value} signal to host {room.host.uid}.', extra={'sid': sid})
