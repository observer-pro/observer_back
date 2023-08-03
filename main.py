import eventlet
import socketio

from models import User, Room, Message

sio = socketio.Server()
app = socketio.WSGIApp(sio)


@sio.event()
def connect(sid, data):
    print(f'{sid} connected')


@sio.on('room/create')
def room_create(sid, data):
    hostname = data.get('name', None)  # no 'name' param in Technical Specification
    user = User(sid, role='host', name=hostname)
    room = Room(host=user)
    room.add_user(user)
    sio.emit('room/update', data=room.get_room_data(), to=sid)


@sio.on('room/join')
def room_join(sid, data):
    room_id = data.get('room_id', None)
    username = data.get('name', None)  # no 'name' param in Technical Specification

    if not room_id:
        sio.emit('room/join', 'Error. No room id present.', to=sid)
        return

    room = Room.get_room_by_id(room_id)
    if not room:
        sio.emit('room/join', 'Error. There is no room with such id.', to=sid)
        return

    user = User(sid, role='client', name=username, room_id=room_id)
    room.add_user(user)

    # Message to User
    sio.emit('room/join', data={'user_id': user.id, 'room_id': room_id}, to=sid)
    # Message to Host
    sio.emit('room/update', data=room.get_room_data(), to=room.host.sid)


@sio.on('message/to_client')
def message_to_client(sid, data):
    send_message(sid, data, 'to_client')


@sio.on('message/to_mentor')
def message_to_mentor(sid, data):
    send_message(sid, data, 'to_mentor')


def send_message(
        sender_sid: str, data: dict, to: str
) -> None:
    """
    Sends a message from the sender to the specified user in a room or host.

    Parameters:
        sender_sid (str): The session ID of the sender.
        data (dict): ...
        to (str): 'to_client' or 'to_mentor'

    Returns:
        None. The function emits the message to the recipient using Socket.IO.
    """
    room_id = data.get('room_id', None)
    content = data.get('content', None)
    receiver_id = data.get('user_id', None)

    if not all((receiver_id, room_id, content)):
        """ Missing some data """
        return

    room = Room.get_room_by_id(room_id)
    receiver = room.get_user_by_id(receiver_id)
    sender = User.get_user_by_sid(sender_sid)

    if not room:
        """ No such Room """
        return

    if not receiver:
        """ No such user in the Room """
        return

    message = Message(sender_id=sender.id, receiver_id=receiver_id, content=content)
    receiver.messages.append(message)

    sio.emit(
        f'message/{to}',
        data={
            'user_id': receiver_id,
            'room_id': room_id,
            'content': content,
            'datetime': message.created_at,
        },
        to=receiver.sid
    )


@sio.on('sharing/start')
def sharing_start(sid, data):
    send_sharing_status(data, command='start')


@sio.on('sharing/end')
def sharing_end(sid, data):
    send_sharing_status(data, command='end')


def send_sharing_status(
        data: dict, command: str
) -> None:
    room_id = data.get('room_id', None)
    receiver_id = data.get('user_id', None)

    room = Room.get_room_by_id(room_id)
    receiver = room.get_user_by_id(receiver_id)

    if not room:
        """ No such Room """
        return

    if not receiver:
        """ No such user in the Room """

    sio.emit(f'sharing/{command}', data={}, to=receiver.sid)


@sio.on('sharing/code_send')
def sharing_code_from_user(sid, data):
    # TODO: нужна ли тут какая-то валидация или всё на фронте и юзер нажимает "Шарить код",
    # TODO: автоматически отправляя хосту по id. Обработка какая-то на бэке нужна?
    room_id = data.get('room_id', None)
    receiver_id = data.get('user_id', None)

    room = Room.get_room_by_id(room_id)
    host = room.get_user_by_id(receiver_id)

    if not room:
        """ No such Room """
        return

    if not host:
        """ Wrong host """

    sio.emit(f'sharing/code_send', data=data, to=host.sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
