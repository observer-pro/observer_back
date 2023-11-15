from socketio import AsyncServer

from src.models import Room, User

from .utils import emit_log, handle_bad_request, parse_files_to_ignore, validate_data


async def send_settings(sio: AsyncServer, sid: str, data: dict) -> None:
    """
    Sends settings to all students in the room.
    Args:
        sio (AsyncServer): The socketio server instance.
        sid (str): The session ID of the user.
        data (dict): The data containing the settings.
    """
    if not await validate_data(sio, data):
        return

    files_to_ignore = data.get('files_to_ignore', None)
    if not files_to_ignore:
        return

    room_id = User.get_user_by_sid(sid).room
    room = Room.get_room_by_id(room_id)

    try:
        result = parse_files_to_ignore(files_to_ignore)
    except Exception as e:
        await handle_bad_request(sio, f'Failed to parse files to ignore: {e}')
        return

    room.settings = result  # Save to the Room.settings

    for student in room.users:
        if student.role == 'client':
            await sio.emit('settings', data=result, to=student.sid)
    # log
    await emit_log(sio, f'The settings were sent to all students in the room {room_id}!')
