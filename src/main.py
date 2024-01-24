import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

from src.components import app
from src.events.ai import register_ai_events
from src.events.connection import register_connection_events
from src.events.message import register_messages_events
from src.events.room import register_room_events
from src.events.settings import register_settings_events
from src.events.sharing_code import register_sharing_code_events
from src.events.steps import register_steps_events

load_dotenv(Path(__file__).parent.parent / '.env')

if os.getenv('SERVER') == 'prod':
    import sentry_sdk

    sentry_sdk.init(os.getenv('GLITCHTIP_DSN'))

register_connection_events()
register_room_events()
register_settings_events()
register_sharing_code_events()
register_messages_events()
register_steps_events()
register_ai_events()

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
