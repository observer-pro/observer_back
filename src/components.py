import asyncio
import logging
import os
from pathlib import Path

import socketio
from dotenv import load_dotenv

from src.web import fast_app

load_dotenv(Path(__file__).parent.parent / '.env')

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', ping_timeout=180)
app = socketio.ASGIApp(sio, other_asgi_app=fast_app)

sio.instrument(
    auth={
        'username': os.getenv('SOCKET_ADMIN_USERNAME'),
        'password': os.getenv('SOCKET_ADMIN_PASSWORD'),
    },
    mode='development',
)


class SocketIOHandler(logging.Handler):
    def __init__(self, sio_server: socketio.AsyncServer, level=logging.NOTSET):
        super().__init__(level)
        self.sio = sio_server

    def emit(self, record):
        try:
            msg = self.format(record)
            sid = record.__dict__.get('sid', None)
            room_id = record.__dict__.get('room_id', None)
            if sid is not None:
                asyncio.create_task(self.sio.emit('log', {'message': msg}, to=sid))
            elif room_id is not None:
                asyncio.create_task(self.sio.emit('log', {'message': msg}, room=room_id))
            else:
                asyncio.create_task(self.sio.emit('log', {'message': msg}))
        except Exception:
            self.handleError(record)


file_handler = logging.FileHandler(Path(__file__).parent.parent / 'log.log')
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

socketio_handler = SocketIOHandler(sio)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.addHandler(socketio_handler)

if os.getenv('SERVER') == 'dev':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
