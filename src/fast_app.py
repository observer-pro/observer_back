from pathlib import Path

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.models import Room

fast_app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@fast_app.get("/roomstats/{room_id}", response_class=HTMLResponse)
async def stats(request: Request, room_id: int):
    room = Room.get_room_by_id(room_id)
    if not room:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": f'Room # {room_id} not found!'},
            status_code=404,
        )

    data = [
        {
            'username': user.name,
            'steps': user.steps,
            'result': round(sum(1 for step in user.steps.values() if step == 'DONE') / len(user.steps) * 100),
        }
        for user in room.users if user.steps
    ]
    if not data:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": f'There are no statistics for Room # {room_id} yet!'},
            status_code=404,
        )

    return templates.TemplateResponse(
        "stats.html",
        {"request": request, "room_id": room_id, "data": data},
    )
