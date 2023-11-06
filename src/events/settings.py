from socketio import AsyncServer

from src.models import Room, User

from .utils import emit_log, validate_data


async def send_settings(sio: AsyncServer, sid: str, data: dict) -> None:
    """
    Sends settings to all students in the room.
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the settings.
    """
    if not await validate_data(sio, data, 'files_to_ignore'):
        return

    files_to_ignore = data.get('files_to_ignore', '')
    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    room.settings = files_to_ignore  # Save settings

    for student in room.users:
        if student.role == 'client':
            await sio.emit('settings', data={'files_to_ignore': files_to_ignore}, to=student.sid)
    # log
    await emit_log(sio, f'The settings were sent to all students in the room {room_id}!')
