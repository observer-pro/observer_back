import logging

from socketio import AsyncServer

from src.models import Room

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('../../log.log')
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


async def validate_data(sio: AsyncServer, data: dict, *keys) -> bool:
    """
    Validate incoming data
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        data (dict): JSON object
        *keys: list of keys to check
    Returns:
        True if keys are present in data and are of correct type.
    """
    if not isinstance(data, dict):
        await handle_bad_request(sio, 'Data should be a JSON object')
        return False

    for key in keys:
        if key not in data:
            await handle_bad_request(sio, f'{key} is not present in data')
            return False
        if key == 'accepted' and not isinstance(data[key], bool):
            await handle_bad_request(sio, f'{key} should be a boolean')
            return False
        if key in ('room_id', 'user_id') and not isinstance(data[key], int):
            await handle_bad_request(sio, f'{key} should be an integer')
            return False
        if key == 'room_id' and not Room.get_room_by_id(data[key]):
            await handle_bad_request(sio, f'No room with id: {data[key]}')
            return False
    return True


async def emit_log(sio: AsyncServer, message: str) -> None:
    """
    Emit a log message.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        message (str): The log message to emit.
    """
    await sio.emit('log', data={'message': message})


async def handle_bad_request(sio: AsyncServer, message: str) -> None:
    """
    Handle bad request by emitting an error event and logging the error message.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        message (str): The error message.
    """
    await sio.emit('error', data={'message': f'400 BAD REQUEST. {message}'})
    logger.error(f'Bad request occurred: {message}')


async def deprecated(sio: AsyncServer, event: str, alternative: str = None) -> None:
    """
    Handle deprecated event by emitting an error event.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        event (str): The deprecated event name.
        alternative (str): An alternative event to use.
    """
    deprecated_message = f'The event "{event}" is deprecated and will be removed in future releases.'
    if alternative:
        deprecated_message += f' Use the event "{alternative}" instead.'
    await sio.emit('error', data={'message': deprecated_message})
