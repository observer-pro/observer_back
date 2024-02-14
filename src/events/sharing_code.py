from src.components import logger, sio
from src.exceptions import RoomNotFoundError, UserNotFoundError
from src.managers import room_manager, user_manager

from .utils import Utils

utils = Utils(sio, logger)


def register_sharing_code_events() -> None:
    @sio.on('sharing/start')
    async def sharing_start(sid, data):
        await send_sharing_start(data)

    @sio.on('sharing/code_send')
    async def sharing_code_send(sid, data):
        await send_sharing_code(sid, data, command='code_send')

    @sio.on('sharing/code_update')
    async def sharing_code_update(sid, data):
        await send_sharing_code(sid, data, command='code_update')

    # deprecated from v1.2.13
    @sio.on('sharing/end')
    async def sharing_end(sid, data):
        await utils.deprecated('sharing/end')


async def send_sharing_start(data: dict) -> None:
    """
    Send sharing/start to a user in a specific room.
    Args:
        data (dict): The data containing the room ID and user ID.
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

    await sio.emit('sharing/end', data={}, room=room_id, skip_sid=user.sid)
    await sio.emit('sharing/start', data={}, to=user.sid)
    logger.debug(f'Host sent sharing/start to the user {user_id}', extra={'sid': room.host.sid})


async def send_sharing_code(sid: str, data: dict, command: str) -> None:
    """
    Send sharing code to the host in the room where the user is.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data to be sent.
        command (str): The command to be sent ('code_send' or 'code_update').
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
    data.update({'user_id': user.uid})

    await sio.emit(f'sharing/{command}', data=data, to=room.host.sid)
    logger.debug(f'User {user.uid} sent sharing/{command} to host {room.host.uid}', extra={'sid': user.sid})
