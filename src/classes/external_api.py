import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / '.env')

url = os.getenv("API_URL")


class ExternalAPIClient:

    @staticmethod
    async def get_solution(data: dict):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    return await response.json()
        except Exception as e:
            return {"status": False, "content": f"An exception occurred: {e}"}
