from socketio import AsyncServer

from src.models import Room, SignalEnum, User

from .utils import deprecated, emit_log, handle_bad_request, validate_data


async def send_sharing_status(sio: AsyncServer, data: dict, command: str) -> None:
    """
    Send sharing status to a user in a specific room.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        data (dict): The data containing the room ID and user ID.
        command (str): The command to send (start or end).
    """
    if not await validate_data(sio, data, 'room_id', 'user_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)

    receiver_id = data.get('user_id')
    receiver = room.get_user_by_id(receiver_id)
    if not receiver:
        await handle_bad_request(sio, f'No such user id {receiver_id} in the room')
        return

    await sio.emit(f'sharing/{command}', data={}, to=receiver.sid)
    # log
    await emit_log(sio, f"Host send '{command}' to the user: {receiver_id}")


async def send_sharing_code(sio: AsyncServer, sid: str, data: dict, command: str) -> None:
    """
    Send sharing code to the host in the specified room.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        sid (str): The session ID of the user.
        data (dict): The data to be sent.
        command (str): The command to be sent ('code_send' or 'code_update').
    """
    if not await validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)
    user = User.get_user_by_sid(sid)
    data.update({'user_id': user.id})

    await sio.emit(f'sharing/{command}', data=data, to=room.host.sid)
    # log
    await emit_log(sio, f'sharing/{command} to host with id: {room.host.id}')


# deprecated from v1.1.0
async def send_signal(sio: AsyncServer, sid: str, data: dict) -> None:
    """
    Send signal to the teacher.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the user ID and one of SignalEnum values.
    """
    if not await validate_data(sio, data, 'user_id'):
        return

    signal_value = data.get('value', None)
    if not signal_value:
        await handle_bad_request(sio, 'No signal received')
        return

    try:
        SignalEnum(signal_value)
    except ValueError:
        await handle_bad_request(sio, f'Invalid signal: {signal_value}')
        return

    user = User.get_user_by_sid(sid)
    user.signal = signal_value
    room = Room.get_room_by_id(user.room)

    await sio.emit('signal', data=data, to=room.host.sid)
    # log
    await emit_log(sio, f'The user {user.id} sent a [{signal_value}] signal to host with id {room.host.id}.')
    await deprecated(sio, 'signal')
