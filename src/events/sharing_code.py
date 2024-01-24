from src.components import logger, sio
from src.managers import room_manager, user_manager

from .utils import Utils

utils = Utils(sio, logger)


def register_sharing_code_events() -> None:
    @sio.on('sharing/start')
    async def sharing_start(sid, data):
        await send_sharing_status(data, command='start')

    @sio.on('sharing/end')
    async def sharing_end(sid, data):
        await send_sharing_status(data, command='end')

    @sio.on('sharing/code_send')
    async def sharing_code_send(sid, data):
        await send_sharing_code(sid, data, command='code_send')

    @sio.on('sharing/code_update')
    async def sharing_code_update(sid, data):
        await send_sharing_code(sid, data, command='code_update')


async def send_sharing_status(data: dict, command: str) -> None:
    """
    Send sharing status to a user in a specific room.
    Args:
        data (dict): The data containing the room ID and user ID.
        command (str): The command to send ('start' or 'end').
    """
    if not await utils.validate_data(data, 'room_id', 'user_id'):
        return

    room_id = data.get('room_id')
    room = room_manager.get_room_by_id(room_id)

    user_id = data.get('user_id')
    receiver = room.get_user_by_id(user_id)
    if not receiver:
        await utils.handle_bad_request(f'No such user id {user_id} in the room')
        return

    await sio.emit(f'sharing/{command}', data={}, to=receiver.sid)
    logger.debug(f'Host send {command} to the user {user_id}')


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
    room = room_manager.get_room_by_id(room_id)
    user = user_manager.get_user_by_sid(sid)
    data.update({'user_id': user.uid})

    await sio.emit(f'sharing/{command}', data=data, to=room.host.sid)
    logger.debug(f'sharing/{command} to host with id: {room.host.uid}')
