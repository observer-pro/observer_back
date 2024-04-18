import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AsyncOpenAI, BadRequestError

load_dotenv(Path(__file__).parent.parent.parent / '.env')

TOKEN = os.getenv('OPENAI_API_KEY')
AI_MODEL = 'gpt-4-1106-preview'


class BaseClient:
    """
    Base class for interacting with the OpenAI API
    """

    @staticmethod
    def _build_prompt(task_text: str, user_solution_code: str) -> str:
        return (
            f'Я выполнил задание (текст задания: "{task_text}")!\n '
            f'Помоги с решением задания и объясни что не так в моём коде (если что-то не так)!\n'
            f'Вот мой код:\n {user_solution_code}'
        )


class AIClient(BaseClient):
    """
    Class for interacting with the OpenAI API
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=TOKEN,
            timeout=10,
            max_retries=3,
        )

    async def _make_request(self, prompt: str) -> dict:
        try:
            completion = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                    },
                ],
            )
            response = completion.choices[0].message.content
            return {'status': True, 'content': response}
        except APIConnectionError as e:
            return {'status': False, 'content': 'The server could not be reached. ' + str(e)}
        except BadRequestError as e:
            return {'status': False, 'content': 'Bad request. ' + str(e)}
        except APIStatusError as e:
            return {'status': False, 'content': str(e.status_code) + ' ' + str(e)}

    async def get_explanation(self, task_text: str, user_solution_code: str) -> dict:
        prompt = self._build_prompt(task_text, user_solution_code)
        return await self._make_request(prompt)


class AlternateAIClient(BaseClient):
    """
    Class for interacting with the OpenAI API
    """

    def __init__(self):
        self.url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json',
        }

    async def _make_request(self, payload: dict) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                ) as response:
                    if response.status == 200:
                        ai_response = await response.json()
                        return {'status': True, 'content': ai_response['choices'][0]['message']['content']}
                    return {'status': False, 'content': f'Something went wrong, response code: {response.status}'}
        except Exception as e:
            return {'status': False, 'content': f'An exception occurred: {e}'}

    async def get_explanation(self, task_text: str, user_solution_code: str) -> dict:
        prompt = self._build_prompt(task_text, user_solution_code)
        payload = {
            'model': AI_MODEL,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
        }
        return await self._make_request(payload)
