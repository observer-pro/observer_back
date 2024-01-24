import os
from pathlib import Path

from dotenv import load_dotenv

from src.components import logger, sio
from src.managers import room_manager, user_manager
from src.models import StatusEnum

from .utils import Utils

load_dotenv(Path(__file__).parent.parent.parent / '.env')

utils = Utils(sio, logger)


def register_connection_events() -> None:
    """Register connection events."""
    sio.on('connect', connect)
    sio.on('disconnect', disconnect_user)
    sio.on('room/kill', room_kill)


async def connect(sid, data):
    if os.getenv('SERVER') == 'dev':
        await utils.create_test_room()
    logger.debug(f'User {sid} connected')


async def disconnect_user(sid: str) -> None:
    """
    Catch user disconnect.
    Args:
        sid (str): The session ID of the user.
    """
    user = user_manager.get_user_by_sid(sid)
    if user and user.room:
        user.status = StatusEnum.OFFLINE
        room = room_manager.get_room_by_id(user.room)

        if user.role == 'host':  # teacher disconnected
            await sio.emit('message', {'message': 'The teacher is offline!'}, room=room.rid)
            logger.debug(f'Teacher {user.uid} disconnected from room id {room.rid})')
        else:  # student disconnected
            await sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
            logger.debug(f'Student {user.uid} disconnected from room {room.rid})')


async def room_kill(sid: str, data: dict) -> None:
    """
    Disconnect user by host with user_id from data.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing 'user_id'.
    """
    if not await utils.validate_data(data, 'user_id'):
        return

    host = user_manager.get_user_by_sid(sid)
    room = room_manager.get_room_by_id(host.room)

    user_id = data.get('user_id')
    user_to_kill = room.get_user_by_id(user_id)
    if not user_to_kill:
        await utils.handle_bad_request(f'No such user with id {user_id} in the room {host.room}')
        return
    await sio.leave_room(user_to_kill.sid, host.room)
    await sio.disconnect(user_to_kill.sid)
