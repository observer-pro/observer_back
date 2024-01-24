from src.exceptions import RoomNotFoundError, UserNotFoundError
from src.models import Room, User


class RoomManager:
    """
    Room Manager to manage rooms
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RoomManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._id = 1000
        self._rooms = {}

    def __repr__(self):
        return f'<{self.__class__.__name__}, rooms count: {len(self._rooms)}>'

    def create_room(self, host: User) -> Room:
        room = Room(self._id, host)
        room.enter_user_to_room(host)
        host.room = self._id
        self._rooms[self._id] = room
        self._id += 1
        return room

    def delete_room(self, room_id: int) -> None:
        try:
            del self._rooms[room_id]
        except KeyError as e:
            raise RoomNotFoundError(f"Room with id '{room_id}' not found.") from e

    def get_room_by_id(self, room_id: int) -> Room | None:
        return self._rooms.get(room_id)

    def get_rooms_log(self) -> dict[str, int | list[dict]]:
        return {
            'total_rooms_count': len(self._rooms),
            'rooms': [
                {'room_id': room.rid, 'users_count': len(room.users), 'host_id': room.host.uid}
                for room in self._rooms.values()
            ],
        }


class UserManager:
    """
    User Manager to manage users
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._id = 100
        self._users = {}

    def __repr__(self):
        return f'<{self.__class__.__name__}, users count: {len(self._users)}>'

    def create_user(self, sid: str, **kwargs) -> User:
        user = User(sid, self._id, **kwargs)
        self._users[sid] = user
        self._id += 1
        return user

    def delete_user(self, sid: str) -> None:
        try:
            del self._users[sid]
        except KeyError as e:
            raise UserNotFoundError(f"User with sid '{sid}' not found.") from e

    def get_user_by_sid(self, sid: str) -> User | None:
        return self._users.get(sid)

    def set_new_sid(self, old_sid: str, new_sid: str) -> User:
        try:
            user = self.get_user_by_sid(old_sid)
            del self._users[old_sid]
            user.sid = new_sid
            self._users[new_sid] = user
            return user
        except KeyError as e:
            raise UserNotFoundError(f"User with sid '{old_sid}' not found.") from e

    def get_all_users(self) -> list[User]:
        return list(self._users.values())


user_manager = UserManager()
room_manager = RoomManager()
