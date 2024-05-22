from pathlib import Path

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.exceptions import RoomNotFoundError
from src.managers import room_manager

fast_app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / 'templates'))


@fast_app.get('/roomstats/{room_id}', response_class=HTMLResponse)
async def stats(request: Request, room_id: int):
    try:
        room = room_manager.get_room_by_id(room_id)
    except RoomNotFoundError:
        return templates.TemplateResponse(
            '404.html',
            {'request': request, 'message': f'Room # {room_id} not found!'},
            status_code=404,
        )
    data = [
        {
            'username': user.name,
            'steps': user.steps,
            'result': round(
                sum(1 for step in user.steps.values() if step in ['DONE', 'ACCEPTED']) / len(user.steps) * 100,
            ),
        }
        for user in room.users.values()
        if user.steps
    ]
    if not data:
        return templates.TemplateResponse(
            '404.html',
            {'request': request, 'message': f'There are no statistics for Room # {room_id} yet!'},
            status_code=404,
        )

    return templates.TemplateResponse(
        'stats.html',
        {'request': request, 'room_id': room_id, 'data': data},
    )
