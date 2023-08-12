import datetime
from typing import Optional


class Room:
    id = 1000
    rooms = {}

    def __init__(self, host):
        self.id: int = type(self).id
        self.users: list[User] = []  # all clients include owner
        self.host: User = host
        self.codecaster: int
        type(self).id += 1
        type(self).rooms[self.id] = self

    def __repr__(self):
        return f'{type(self).__name__}, users: {self.users}'

    def add_user(self, user: 'User'):
        self.users.append(user)

    def serialize_users(self, users: list['User']) -> list[dict[str, ...]]:
        serialized_users = []
        for user in users:
            serialized_user = {
                'id': user.id,
                'sid': user.sid,
                'room': user.room,
                'name': user.name,
                'role': user.role,
                'messages': [message.serialize() for message in user.messages],
            }
            serialized_users.append(serialized_user)
        return serialized_users

    def get_room_data(self) -> dict:
        return {
            'id': self.id,
            'users': self.serialize_users(self.users),
            'host': self.host.id,
            'codecaster': None,
        }

    def get_user_by_id(self, user_id: int | None) -> Optional['User']:
        if not user_id:
            return None
        for user in self.users:
            if user_id == user.id:
                return user
        return None

    @classmethod
    def get_room_by_id(cls, room_id: int) -> Optional['Room']:
        return cls.rooms.get(room_id)

    @classmethod
    def delete_room(cls, room_id: int) -> None:
        if room_id in cls.rooms:
            del cls.rooms[room_id]


class User:
    id = 100
    users = {}

    def __init__(self, sid, name=None, room_id=None, role='client'):
        self.id: int = type(self).id
        self.sid: str = sid
        self.room: int = room_id
        self.name: str = name
        self.role: str = role
        self.messages: list[Message] = []
        type(self).id += 1
        type(self).users[self.sid] = self

    def __repr__(self):
        return f'{type(self).__name__} obj, messages: {self.messages}'

    @classmethod
    def get_user_by_sid(cls, sid: str) -> Optional['User']:
        return cls.users.get(sid)


class Message:
    def __init__(self, sender_id, receiver_id, content):
        self.sender: int = sender_id
        self.receiver: int = receiver_id
        self.content: str = content
        self.status: str | None = None
        current_time = datetime.datetime.now().time()
        self.created_at: str = current_time.strftime('%H:%M:%S')

    def __repr__(self):
        return f'{self.content}'

    def serialize(self) -> dict[str, ...]:
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at,
        }
