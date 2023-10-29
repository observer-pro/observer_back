import socketio

from models import Room, User

from .utils import emit_log, validate_data


async def send_settings(sio: socketio.AsyncServer, data: dict, sid: str) -> None:
    """
    Sends settings to all students in the room.
    Args:
        sio (socketio.AsyncServer): The socketio server instance.
        data (dict): The data containing the settings.
        sid (str): The session ID of the user.
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
