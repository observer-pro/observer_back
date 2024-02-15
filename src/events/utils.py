import logging
import re
from enum import Enum

from socketio import AsyncServer

from src.config import PLUGIN_VERSION
from src.exceptions import RoomNotFoundError
from src.managers import room_manager, user_manager


class AlertsEnum(Enum):
    INFO = 'INFO'
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class Utils:
    def __init__(self, sio: AsyncServer, logger: logging.Logger):
        self.sio = sio
        self.logger = logger

    async def validate_data(self, data: dict, *keys) -> bool:
        """
        Validate incoming data
        Args:
            data (dict): JSON object
            *keys: list of keys to check
        Returns:
            True if keys are present in data and are of correct type.
        """
        if not isinstance(data, dict):
            await self.handle_bad_request('Data should be a JSON object')
            return False

        for key in keys:
            if key not in data:
                await self.handle_bad_request(f'{key} is not present in data')
                return False
            if key == 'accepted' and not isinstance(data[key], bool):
                await self.handle_bad_request(f'{key} should be a boolean')
                return False
            if key in ('room_id', 'user_id') and not isinstance(data[key], int):
                await self.handle_bad_request(f'{key} should be an integer')
                return False
        return True

    async def check_version(self, sid: str, version: str | None) -> None:
        """
        Check if the client version is outdated.
        Args:
            sid (str): The session ID of the user.
            version (str | None): The version string.
        """
        if version is not None:
            current_version = [int(part) for part in PLUGIN_VERSION.split('.') if part.isdigit()]
            version_of_user_plugin = [int(part) for part in version.split('.') if part.isdigit()]

            if current_version > version_of_user_plugin:
                await self.alerts(
                    sid,
                    f'You have an outdated version of the plugin. '
                    f'Please install the latest version {PLUGIN_VERSION}',
                    AlertsEnum.WARNING,
                )

    async def handle_bad_request(self, message: str) -> None:
        """
        Handle bad request by emitting an error event and logging the error message.
        Args:
            message (str): The error message.
        """
        await self.sio.emit('error', data={'message': f'Error: {message}'})
        self.logger.error('Error: %s', message)

    async def deprecated(self, event: str, alternative: str = None) -> None:
        """
        Handle deprecated event by emitting an error event.
        Args:
            event (str): The deprecated event name.
            alternative (str): An alternative event to use.
        """
        deprecated_message = f'The event "{event}" is deprecated and will be removed in future releases.'
        if alternative:
            deprecated_message += f' Use the event "{alternative}" instead.'
        await self.sio.emit('error', data={'message': deprecated_message})

    async def alerts(self, sid: str, message: str, allert_type: AlertsEnum) -> None:
        """
        Emit an alert message.
        Args:
            sid (str): The session ID of the user.
            message (str): The alert message to emit.
            allert_type (str): The type of the alert (INFO, SUCCESS, WARNING, ERROR)
        """
        await self.sio.emit('alerts', data={'message': message, 'type': allert_type.name}, to=sid)

    async def create_test_room(self) -> None:
        """Create room for tests"""
        try:
            room_manager.get_room_by_id(1000)
        except RoomNotFoundError:
            user = user_manager.create_user('TESTROOMHOST', name='Mama Zmeya', role='host')
            test_room = room_manager.create_room(host=user)
            self.logger.debug('Test room created with id: %s', test_room.rid)


def parse_files_to_ignore(data: str) -> dict[str : list[str]]:
    """
    Parses a string with names and break lines to ignore and returns a dictionary
    containing the names, directories, and extensions.
    Args:
        data (str): The string of file names, directories and extensions to ignore.
    Returns:
        dict: A dictionary containing the names, directories, and extensions.

    """
    pattern = re.compile(r'^[a-zA-Z0-9*./_\[\]\-$]+')
    data = {i.strip() for i in data.split('\n') if '#' not in i}
    names, directories, extensions = [], [], []

    for name in data:
        if not pattern.match(name) or name.count('/') > 1 or '*$' in name:
            continue
        if name.startswith('/') or name.endswith('/'):
            directories.append(name.replace('*', '').replace('/', ''))
        elif '*.' in name:
            extensions.append(name.replace('*.', ''))
        else:
            names.append(name)

    return {'names': names, 'dirs': directories, 'extensions': extensions}
