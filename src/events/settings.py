from src.components import logger, sio
from src.managers import room_manager, user_manager

from .utils import Utils, parse_files_to_ignore

utils = Utils(sio, logger)


def register_settings_events() -> None:
    @sio.on('settings')
    async def send_settings(sid: str, data: dict) -> None:
        """
        Sends settings to all students in the room.
        Args:
            sid (str): The session ID of the user.
            data (dict): The data containing the settings.
        """
        if not await utils.validate_data(data):
            return

        files_to_ignore = data.get('files_to_ignore', None)
        if files_to_ignore is None:
            return

        host = user_manager.get_user_by_sid(sid)
        room = room_manager.get_room_by_id(host.room)

        try:
            result = parse_files_to_ignore(files_to_ignore)
        except Exception as e:
            await utils.handle_bad_request(f'Failed to parse files to ignore: {e}')
            return

        room.settings = result  # Save to the Room.settings
        await sio.emit('settings', data=result, room=host.room)
        logger.debug(f'Settings were sent to all students in the room {host.room}!')
