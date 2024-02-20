import os
from pathlib import Path

from dotenv import load_dotenv

from src.components import logger, sio
from src.exceptions import RoomNotFoundError, UserNotFoundError
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
    logger.debug(f'User {sid} connected', extra={'sid': sid})


async def disconnect_user(sid: str) -> None:
    """
    Catch user disconnect.
    Args:
        sid (str): The session ID of the user.
    """
    try:
        user = user_manager.get_user_by_sid(sid)
    except UserNotFoundError:
        return

    if user and user.room:
        user.status = StatusEnum.OFFLINE
        try:
            room = room_manager.get_room_by_id(user.room)
            if user.role != 'host':
                room.remove_user_from_room(user.uid)  # contradicts with room/rejoin (not realised on plugin)
        except RoomNotFoundError:
            await utils.handle_bad_request(f'Room {user.room} not found.')
            return
        except UserNotFoundError:
            await utils.handle_bad_request(f'Something went wrong with removing user {user.uid} from room.')
            return

        if user.role == 'host':  # teacher disconnected
            await sio.emit('message', {'message': 'The teacher is offline!'}, room=room.rid)
            logger.debug(f'Teacher {user.uid} disconnected from room id {room.rid})', extra={'room_id': room.rid})
        else:  # student disconnected
            await sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)
            logger.debug(f'Student {user.uid} disconnected from room {room.rid})', extra={'sid': room.host.sid})


async def room_kill(sid: str, data: dict) -> None:
    """
    Disconnect user by host with user_id from data.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing 'user_id'.
    """
    if not await utils.validate_data(data, 'user_id'):
        return

    user_id = data.get('user_id')
    try:
        host = user_manager.get_user_by_sid(sid)
        if host.role != 'host':
            raise UserNotFoundError
        room_id = host.room
        room = room_manager.get_room_by_id(room_id)
        user_to_kill = room.get_user_by_id(user_id)
        await sio.leave_room(user_to_kill.sid, room_id)
        await sio.disconnect(user_to_kill.sid)
    except UserNotFoundError:
        await utils.handle_bad_request(f'User {user_id} not found.')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request('Room not found.')
        return
