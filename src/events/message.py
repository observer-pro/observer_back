from socketio import AsyncServer

from src.models import Message, Room, User

from .utils import emit_log, handle_bad_request, validate_data


async def send_message(sio: AsyncServer, sender_sid: str, data: dict, to: str) -> None:
    """
    Sends a message from the host to the specified user in a room and vice versa.
    Args:
        sio (AsyncServer): The Socket.IO server instance.
        sender_sid (str): The session ID of the user.
        data (dict): The data containing the 'room_id' and 'user_id' and 'content'
        to (str):
            'to_client' - from host to user
            'to_mentor' - from user to host
    """
    if not await validate_data(sio, data, 'room_id'):
        return

    room_id = data.get('room_id')
    room = Room.get_room_by_id(room_id)
    content = data.get('content', '')

    if to == 'to_client':
        receiver_id = data.get('user_id', None)
        receiver = room.get_user_by_id(receiver_id)

        if not receiver:
            await handle_bad_request(sio, f'No such user id {receiver_id} in the room')
            return
    else:
        receiver_id = room.host.id
        receiver = room.host

    sender = User.get_user_by_sid(sender_sid)
    message = Message(sender_id=sender.id, receiver_id=receiver_id, content=content)

    if to == 'to_client':
        receiver.messages.append(message)
    else:
        sender.messages.append(message)

    await sio.emit(
        f'message/{to}',
        data={
            'user_id': receiver_id if to == 'to_client' else sender.id,
            'room_id': room_id,
            'content': content,
            'datetime': message.created_at,
        },
        to=receiver.sid,
    )
    # log
    await emit_log(sio, f'User {sender.id} has sent message to user: {receiver_id}')


async def send_user_messages(sio: AsyncServer, sid: str, data: dict) -> None:
    """
    Send user messages.
    Parameters:
        sio (AsyncServer): The Socket.IO server instance.
        sid (str): The session ID of the client.
        data (dict): The data containing the 'user_id'
    Returns:
        None
    """
    if not await validate_data(sio, data, 'user_id'):
        return

    user_id = data.get('user_id')

    host = User.get_user_by_sid(sid)
    room = Room.get_room_by_id(host.room)
    if not room:
        await handle_bad_request(sio, f'No such room with id {host.room}!')
        return

    user = room.get_user_by_id(user_id)
    if not user:
        await handle_bad_request(sio, f'No such user with id {user_id} in the Room {host.room}!')
        return

    user_messages = User.get_user_messages(user.sid)

    await sio.emit('message/user', data={'user_id': user_id, 'messages': user_messages}, to=sid)
