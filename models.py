from datetime import datetime, timezone
from enum import Enum
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

    @staticmethod
    def serialize_users(users: list['User']) -> list[dict[str, ...]]:
        serialized_users = []
        for user in users:
            if user.status == StatusEnum.OFFLINE:
                continue
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

    def remove_user_from_room(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        if user in self.users:
            user.room = None
            self.users.remove(user)
            return True
        return False

    @classmethod
    def get_room_by_id(cls, room_id: int) -> Optional['Room']:
        return cls.rooms.get(room_id)

    @classmethod
    def delete_room(cls, room_id: int) -> None:
        room = cls.get_room_by_id(room_id)
        if room:
            for user in room.users:
                del User.users[user.sid]
            del cls.rooms[room_id]


class StatusEnum(Enum):
    OFFLINE = 'offline'
    ONLINE = 'online'


class User:
    id = 100
    users = {}

    def __init__(self, sid, name=None, room_id=None, role='client', status=StatusEnum.ONLINE):
        self.id: int = type(self).id
        self.sid: str = sid
        self.room: int = room_id
        self.name: str = name
        self.role: str = role
        self.status: StatusEnum = status
        self.messages: list[Message] = []
        type(self).id += 1
        type(self).users[self.sid] = self

    def __repr__(self):
        return f'{type(self).__name__} obj, sid: {self.sid}'

    def set_new_sid(self, sid: str) -> None:
        del type(self).users[self.sid]
        self.sid = sid
        type(self).users[self.sid] = self

    @classmethod
    def get_user_by_sid(cls, sid: str) -> Optional['User']:
        return cls.users.get(sid)


class Message:
    def __init__(self, sender_id, receiver_id, content):
        self.sender: int = sender_id
        self.receiver: int = receiver_id
        self.content: str = content
        self.status: str | None = None
        current_time = datetime.now(timezone.utc).time()
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
