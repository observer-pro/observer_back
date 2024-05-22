from src.classes.external_api import ExternalAPIClient
from src.components import logger, sio

from .utils import Utils

utils = Utils(sio, logger)


def register_ai_events() -> None:
    """Register AI events."""
    sio.on('solution/ai', solution_from_ai)


async def solution_from_ai(sid: str, data: dict[str, str]) -> None:
    """
    Sends a solution from the AI to the student with the given sid.
    Args:
        sid (str): The session ID of the user.
        data (dict): The data containing the solution.
    """
    event = 'solution/ai'

    if not await utils.validate_data(data):
        return
    content = data.get('content')
    code = data.get('code')
    if not content or not code:
        await utils.handle_bad_request(f'Event: {event}. Task content and code are required!')
        return
    logger.debug('Code with a question were sent to AI', extra={'sid': sid})

    client = ExternalAPIClient()
    ai_response: dict = await client.get_solution({'content': content, 'code': code})

    if not ai_response['status']:
        await utils.handle_bad_request(ai_response['content'])
        return

    await sio.emit('solution/ai', data={'content': ai_response['content']}, to=sid)
    logger.debug(f'The AI solution was sent to the user with SID {sid}!', extra={'sid': sid})
