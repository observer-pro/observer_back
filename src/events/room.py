import asyncio
from random import choice

from src.components import logger, sio
from src.exceptions import RoomNotFoundError, UserNotFoundError
from src.managers import room_manager, user_manager
from src.models import StatusEnum

from .utils import AlertsEnum, Utils

utils = Utils(sio, logger)


def register_room_events() -> None:
    """Register room events."""
    sio.on('room/create', room_create)
    sio.on('room/join', room_join)
    sio.on('room/leave', room_leave)
    sio.on('room/close', room_close)
    sio.on('room/log', room_log)

    @sio.on('room/rejoin')
    async def room_rejoin(sid, data):
        await reconnect(sid, data, command='rejoin')

    @sio.on('room/rehost')
    async def room_rehost(sid, data):
        await reconnect(sid, data, command='rehost')


async def room_create(sid: str, data: dict) -> None:
    """
    Create a room by host.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing the host name.
    """
    if not await utils.validate_data(data):
        return

    hostname = data.get('name')
    user = user_manager.create_user(sid, name=hostname, role='host')
    room = room_manager.create_room(host=user)
    await sio.emit('room/update', data=room.get_room_data(), to=sid)
    logger.debug(f'User {user.uid} created room {room.rid}!', extra={'sid': sid})


async def room_join(sid: str, data: dict) -> None:
    """
    Join a user to a room.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing room_id.
    """
    if not await utils.validate_data(data, 'room_id'):
        return

    version = data.get('version')
    await utils.check_version(sid, version)

    room_id = data.get('room_id')
    try:
        room = room_manager.get_room_by_id(room_id)
        user = user_manager.get_user_by_sid(sid)
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Room {room_id} not found!')
        return
    except UserNotFoundError:
        user = None

    if user and user.room is not None:
        await utils.handle_bad_request(f'User {user.uid} already in room {user.room}!')
        return

    username = data.get('name', 'Guest' + ''.join(choice('0123456789') for _ in range(10)))
    if username in room.usernames:
        await utils.alerts(
            sid,
            f'Username {username} is already used in room {room_id}!',
            AlertsEnum.ERROR,
        )
        await utils.handle_bad_request(f'Username {username} is already used in room {room_id}!')
        return

    user = user_manager.create_user(sid, name=username, role='client', room_id=room_id)
    room.save_username(username)
    room.add_user_to_room(user)
    await sio.enter_room(sid, room_id)

    # Message to student
    await sio.emit('room/join', data={'user_id': user.uid, 'room_id': room_id}, to=sid)

    # Deprecated from v1.1.0
    if room.exercise:
        await sio.emit('exercise', data={'content': room.exercise}, to=sid)
        logger.debug(f'The exercise was sent to the student {user.uid})!')

    # If steps exists, send it to student
    if room.steps:
        await sio.emit('steps/all', data=room.steps, to=sid)
        logger.debug(f'The steps were sent to the student {user.uid})!')

    # If settings exists, send it to student
    if room.settings:
        await sio.emit('settings', data=room.settings, to=sid)
        logger.debug(f'The settings were sent to the student {user.uid}!')

    # Update data for teacher
    await sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
    logger.debug(f'User {user.uid} has joined the room {room_id}!', extra={'sid': sid})


async def reconnect(sid: str, data: dict, command: str) -> None:
    """
    Rejoin a user to a room (host or student).
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing room_id and user_id.
        command (str): The command to execute ('rejoin' or 'rehost').
    """
    if not await utils.validate_data(data, 'room_id', 'user_id'):
        return

    room_id = data.get('room_id')
    user_id = data.get('user_id')
    try:
        room = room_manager.get_room_by_id(room_id)
        user = room.get_user_by_id(user_id)
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Room {room_id} not found!')
        return
    except UserNotFoundError:
        await utils.handle_bad_request(f'User {user_id} in room {room_id} not found!')
        return

    try:
        user = user_manager.set_new_sid(old_sid=user.sid, new_sid=sid)  # Save the new SID after reconnect
        user.status = StatusEnum.ONLINE  # Update user status
    except UserNotFoundError:
        await utils.handle_bad_request(f"Can't change SID. User with id '{user_id}' not found.")
        return

    if command == 'rejoin':  # Student rejoin
        await sio.enter_room(sid, room_id)
        await sio.emit('room/join', data={'user_id': user.uid, 'room_id': room_id}, to=sid)
        logger.debug(f'User {user.name} with id {user_id} reconnected!', extra={'sid': sid})
    else:  # Teacher rehost
        # Send messages to students
        await sio.emit('message', {'message': 'The teacher reconnected!'}, room=room_id)
        await sio.emit('sharing/end', data={}, room=room_id)
        # Send imported steps to host if they exist
        if room.steps:
            await sio.emit('steps/load', data=room.steps, to=room.host.sid)
        logger.debug(f'Host {user.name} with id {user_id} reconnected!', extra={'sid': room.host.sid})

    # Update data for teacher
    await sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)


async def room_leave(sid: str, data: dict) -> None:
    """
    Leave a room.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing room_id.
    """
    if not await utils.validate_data(data, 'room_id'):
        return

    room_id = data.get('room_id')
    try:
        room = room_manager.get_room_by_id(room_id)
        user = user_manager.get_user_by_sid(sid)
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Room {room_id} not found!')
        return
    except UserNotFoundError:
        await utils.handle_bad_request(f'User with sid {sid} not found!')
        return

    try:
        room.remove_user_from_room(user.uid)
    except UserNotFoundError:
        await utils.handle_bad_request(f'User is not in the room {room_id}')
        return

    try:
        await sio.leave_room(sid, room_id)
        user_manager.delete_user(sid)
    except UserNotFoundError:
        await utils.handle_bad_request(f"Something went wrong. Can't leave the room {room_id}!")
        return
    await sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
    logger.debug(f'User {user.uid} has left the room {room_id}!', extra={'sid': room.host.sid})


async def room_close(sid: str, data: dict) -> None:
    """
    Close a room by host.
    Args:
        sid (str): not using.
        data (dict): The data containing 'room_id'.
    """
    if not await utils.validate_data(data, 'room_id'):
        return

    try:
        user = user_manager.get_user_by_sid(sid)
        if user.role != 'host':
            await utils.handle_bad_request(f'User with sid {sid} has no rights to close the room!')
            return
    except UserNotFoundError:
        await utils.handle_bad_request(f'User with sid {sid} not found!')
        return

    room_id = data.get('room_id')
    # Send room/closed to students
    await sio.emit('room/closed', {'message': 'Room closed!'}, room=room_id)

    await asyncio.sleep(2)
    await sio.close_room(room_id)
    try:
        room = room_manager.get_room_by_id(room_id)
        for user in room.users.values():
            try:
                user_manager.delete_user(user.sid)
            except UserNotFoundError:
                pass
        room_manager.delete_room(room_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'User with sid {sid} not found!')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Room {room_id} not found!')
        return
    logger.debug(f'Room {room_id} has been closed!')  # TODO sent to host or not?


async def room_log(sid: str, data: dict) -> None:
    """
    Send room log.
    Args:
        sid (str): The session ID of the user.
        data (dict): not using.
    """
    log = room_manager.get_rooms_log()
    log.update(
        {'users': [f'Room {user.room}: {user.name}, {user.status.name}' for user in user_manager.get_all_users()]}
    )
    await sio.emit('room/log', data=log, to=sid)
