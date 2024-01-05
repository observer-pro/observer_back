import os
from pathlib import Path

import socketio
import uvicorn
from dotenv import load_dotenv

from src.events.exercise import (
    import_steps_from_notion,
    send_exercise,
    send_exercise_feedback,
    send_exercise_reset,
    send_solution_from_ai,
    send_statuses_from_host,
    send_statuses_from_student,
    send_steps_from_host,
    send_table,
)
from src.events.message import send_message, send_user_messages
from src.events.room import (
    close_room,
    create_room,
    create_test_room,
    disconnect_user,
    disconnect_user_by_host,
    exit_from_room,
    join_to_room,
    rejoin,
    room_log,
)
from src.events.settings import send_settings
from src.events.sharing import send_sharing_code, send_sharing_status, send_signal
from src.events.utils import emit_log
from src.fast_app import fast_app

load_dotenv(Path(__file__).parent.parent / '.env')

if os.getenv('SERVER') == 'prod':
    import sentry_sdk

    GLITCHTIP_DSN = os.getenv('GLITCHTIP_DSN')
    sentry_sdk.init(GLITCHTIP_DSN)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', ping_timeout=180)
app = socketio.ASGIApp(sio, other_asgi_app=fast_app)


@sio.event
async def connect(sid, data):
    await create_test_room(sio, sid)
    # log
    await emit_log(sio, f'User {sid} connected')


@sio.event
async def disconnect(sid):
    await disconnect_user(sio, sid)


@sio.on('room/create')
async def room_create(sid, data):
    await create_room(sio, sid, data)


@sio.on('room/join')
async def room_join(sid, data):
    await join_to_room(sio, sid, data)


@sio.on('room/leave')
async def room_leave(sid, data):
    await exit_from_room(sio, sid, data)


@sio.on('room/kill')
async def room_kill(sid, data):
    await disconnect_user_by_host(sio, sid, data)


@sio.on('signal')
async def signal(sid, data):
    await send_signal(sio, sid, data)


@sio.on('message/to_client')
async def message_to_client(sid, data):
    await send_message(sio, sid, data, 'to_client')


@sio.on('message/to_mentor')
async def message_to_mentor(sid, data):
    await send_message(sio, sid, data, 'to_mentor')


@sio.on('message/user')
async def user_messages(sid, data):
    await send_user_messages(sio, sid, data)


@sio.on('sharing/start')
async def sharing_start(sid, data):
    await send_sharing_status(sio, data, command='start')


@sio.on('sharing/end')
async def sharing_end(sid, data):
    await send_sharing_status(sio, data, command='end')


@sio.on('sharing/code_send')
async def sharing_code_send(sid, data):
    await send_sharing_code(sio, sid, data, command='code_send')


@sio.on('sharing/code_update')
async def sharing_code_update(sid, data):
    await send_sharing_code(sio, sid, data, command='code_update')


# deprecated from the v1.1.0
@sio.on('exercise')
async def exercise(sid, data):
    await send_exercise(sio, sid, data)


@sio.on('exercise/feedback')
async def exercise_feedback(sid, data):
    await send_exercise_feedback(sio, data)


@sio.on('exercise/reset')
async def exercise_reset(sid, data):
    await send_exercise_reset(sio, sid)


@sio.on('solution/ai')
async def solution_ai(sid, data):
    await send_solution_from_ai(sio, sid, data)


@sio.on('steps/all')
async def steps_all(sid, data):
    await send_steps_from_host(sio, sid, data)


@sio.on('steps/status/to_client')
async def steps_status_to_client(sid, data):
    await send_statuses_from_host(sio, sid, data)


@sio.on('steps/status/to_mentor')
async def steps_status_to_mentor(sid, data):
    await send_statuses_from_student(sio, sid, data)


@sio.on('steps/table')
async def steps_table(sid, data):
    await send_table(sio, sid)


@sio.on('steps/import')
async def steps_import(sid, data):
    await import_steps_from_notion(sio, sid, data)


@sio.on('settings')
async def sharing_settings(sid, data):
    await send_settings(sio, sid, data)


@sio.on('room/rejoin')
async def room_rejoin(sid, data):
    await rejoin(sio, sid, data, command='rejoin')


@sio.on('room/rehost')
async def room_rehost(sid, data):
    await rejoin(sio, sid, data, command='rehost')


@sio.on('room/close')
async def room_close(sid, data):
    await close_room(sio, data)


# JUST FOR TESTS
@sio.on('room/log')
async def room_data(sid, data):
    await room_log(sio, sid)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
