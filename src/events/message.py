from src.components import logger, sio
from src.exceptions import RoomNotFoundError, UserNotFoundError
from src.managers import room_manager, user_manager
from src.models import Message

from .utils import Utils

utils = Utils(sio, logger)


def register_messages_events() -> None:
    """Register message events."""
    sio.on('message/user', load_user_messages)

    @sio.on('message/to_client')
    async def message_to_client(sid, data):
        await send_message(sid, data, 'to_client')

    @sio.on('message/to_mentor')
    async def message_to_mentor(sid, data):
        await send_message(sid, data, 'to_mentor')


async def send_message(sender_sid: str, data: dict, to: str) -> None:
    """
    Sends a message from the host to the specified user in a room and vice versa.
    Args:
        sender_sid (str): The session ID of the user.
        data (dict): The data containing the 'room_id' and 'user_id' and 'content'
        to (str):
            'to_client' - from host to user
            'to_mentor' - from user to host
    """
    event = f'message/{to}'

    if not await utils.validate_data(data, 'room_id'):
        return

    room_id = data.get('room_id')
    content = data.get('content', '')
    try:
        room = room_manager.get_room_by_id(room_id)
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Room {room_id} not found.')
        return

    if to == 'to_client':
        receiver_id = data.get('user_id')
        try:
            receiver = room.get_user_by_id(receiver_id)
        except UserNotFoundError:
            await utils.handle_bad_request(f'Event: {event}. User {receiver_id} in room {room_id} not found.')
            return
    else:  # to_mentor
        receiver_id = room.host.uid
        receiver = room.host

    try:
        sender = user_manager.get_user_by_sid(sender_sid)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. User {sender_sid} (sender) not found.')
        return

    message = Message(sender_id=sender.uid, receiver_id=receiver_id, content=content)

    if to == 'to_client':
        receiver.messages.append(message)
    else:
        sender.messages.append(message)

    await sio.emit(
        f'message/{to}',
        data=message.serialize(),
        to=receiver.sid,
    )
    logger.debug(f'User {sender.uid} sent message to user {receiver_id}', extra={'sid': sender.sid})


async def load_user_messages(sid: str, data: dict) -> None:
    """
    Send user messages.
    Parameters:
        sid (str): The session ID of the client.
        data (dict): The data containing the 'user_id'
    """
    event = 'message/user'

    if not await utils.validate_data(data, 'user_id'):
        return

    user_id = data.get('user_id')

    try:
        host = user_manager.get_user_by_sid(sid)
        room = room_manager.get_room_by_id(host.room)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. Host with sid {sid} not found.')
        return
    except RoomNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. These host has no room.')
        return

    try:
        user = room.get_user_by_id(user_id)
    except UserNotFoundError:
        await utils.handle_bad_request(f'Event: {event}. User with id {user_id} in room {host.room} not found!')
        return

    user_messages = user.get_user_messages()
    await sio.emit('message/user', data={'user_id': user_id, 'messages': user_messages}, to=sid)
    logger.debug(f'User {user_id} messages have been sent to the host {host.uid}', extra={'sid': sid})
