from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Room:
    def __init__(self, room_id: int, host: 'User'):
        self.rid = room_id
        self.host = host
        self.users: list[User] = []  # all clients include owner
        self.settings: dict[str : list[str]] = {}
        self.steps: list[dict[str, str]] = []
        self.exercise: str = ''  # deprecated from the v1.1.0

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.rid}, users count: {len(self.users)}>'

    def enter_user_to_room(self, user: 'User'):
        self.users.append(user)

    @staticmethod
    def serialize_users(users: list['User']) -> list[dict[str, ...]]:
        serialized_users = []
        for user in users:
            if user.status == StatusEnum.OFFLINE:
                continue
            serialized_user = {
                'id': user.uid,
                'sid': user.sid,
                'room': user.room,
                'name': user.name,
                'role': user.role,
                'steps': user.steps,
                # 'messages': [message.serialize() for message in user.messages],  # deprecated from the v1.2.0
            }
            serialized_users.append(serialized_user)
        return serialized_users

    def get_room_data(self) -> dict:
        return {
            'id': self.rid,
            'users': self.serialize_users(self.users),
            'host': self.host.uid,
        }

    def get_user_by_id(self, user_id: int | None) -> Optional['User']:
        if not user_id:
            return None
        for user in self.users:
            if user_id == user.uid:
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


class StatusEnum(Enum):
    OFFLINE = 'offline'
    ONLINE = 'online'


class SignalEnum(Enum):
    NONE = 'NONE'
    IN_PROGRESS = 'IN_PROGRESS'
    HELP = 'HELP'
    DONE = 'DONE'


class User:
    def __init__(
        self,
        sid,
        uid,
        name=None,
        room_id=None,
        role='client',
        signal=SignalEnum.NONE,
        status=StatusEnum.ONLINE,
    ):
        self.sid: str = sid
        self.uid: int = uid
        self.name: str = name
        self.room: int = room_id
        self.role: str = role
        self.status: StatusEnum = status
        self.steps: dict[str:str] = {}
        self.messages: list[Message] = []
        self.signal: SignalEnum = signal  # deprecated from the v1.1.0

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.uid}, name: {self.name}, status: {self.status.name}>'

    def get_user_messages(self) -> Optional[list[dict[str, ...]]]:
        return [message.serialize() for message in self.messages]


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
