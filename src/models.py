from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.exceptions import UserNotFoundError


class Room:
    """Room Class"""

    __slots__ = ('rid', 'host', 'users', 'usernames', 'settings', 'steps', 'exercise')

    def __init__(self, room_id: int, host: 'User'):
        self.rid = room_id
        self.host = host
        self.users: dict[int, User] = {host.uid: host}
        self.usernames: list[str] = []
        self.settings: dict[str : list[str]] = {}
        self.steps: list[dict[str, str]] = []
        self.exercise: str = ''  # deprecated from the v1.1.0

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.rid}, users count: {len(self.users)}>'

    def serialize_users(self) -> list[dict[str, ...]]:
        return [user.serialize() for user in self.users.values() if user.status != StatusEnum.OFFLINE]

    def get_room_data(self) -> dict:
        return {
            'id': self.rid,
            'users': self.serialize_users(),
            'host': self.host.uid,
        }

    def get_user_by_id(self, user_id: int | None) -> 'User':
        try:
            return self.users[user_id]
        except KeyError:
            raise UserNotFoundError() from None

    def save_username(self, username: str) -> None:
        self.usernames.append(username)

    def add_user_to_room(self, user: 'User') -> None:
        self.users[user.uid] = user

    def remove_user_from_room(self, user_id: int) -> None:
        try:
            user = self.users[user_id]
            user.room = None
            self.usernames.remove(user.name)
            del self.users[user_id]
        except (KeyError, ValueError):
            raise UserNotFoundError() from None


class StatusEnum(Enum):
    OFFLINE = 'offline'
    ONLINE = 'online'


class SignalEnum(Enum):
    NONE = 'NONE'
    IN_PROGRESS = 'IN_PROGRESS'
    HELP = 'HELP'
    DONE = 'DONE'


class User:
    """User Class"""

    __slots__ = ('sid', 'uid', 'name', 'room', 'role', 'status', 'steps', 'messages', 'signal')

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

    def serialize(self) -> dict[str, ...]:
        return {
            'id': self.uid,
            'sid': self.sid,
            'room': self.room,
            'name': self.name,
            'role': self.role,
            'steps': self.steps,
        }

    def get_user_messages(self) -> Optional[list[dict[str, ...]]]:
        return [message.serialize() for message in self.messages]


class Message:
    """Message Class"""

    __slots__ = ('sender', 'receiver', 'content', 'status', 'created_at')

    def __init__(self, sender_id, receiver_id, content):
        self.sender: int = sender_id
        self.receiver: int = receiver_id
        self.content: str = content
        self.status: str | None = None
        current_time = datetime.now(timezone.utc).time()
        self.created_at: str = current_time.strftime('%H:%M:%S')

    def __repr__(self):
        return f'<{self.__class__.__name__}, sender: {self.sender}, receiver: {self.receiver}>'

    def serialize(self) -> dict[str, ...]:
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at,
        }
