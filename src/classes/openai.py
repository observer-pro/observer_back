import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncClient

load_dotenv(Path(__file__).parent.parent.parent / '.env')

client = AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))


class AIClient:
    """
    Class for interacting with the OpenAI API
    """

    @staticmethod
    def _build_prompt(task_text: str, user_solution_code: str) -> str:
        prompt = (f'Я выполнил задание (текст задания: "{task_text}")!\n '
                  f'Помоги с решением задания и объясни что не так в моём коде (если что-то не так)!\n'
                  f'Вот мой код:\n {user_solution_code}')
        return prompt

    @staticmethod
    async def _make_request(prompt: str) -> str:
        completion = await client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        try:
            response = completion.choices[0].message.content
            return response
        except Exception as e:
            return str(e)

    async def get_explanation(self, task_text: str, user_solution_code: str) -> str:
        print(f'OpenAI API key: {os.getenv("OPENAI_API_KEY")[:-10] + "*"*10}')
        prompt = self._build_prompt(task_text, user_solution_code)
        ai_response = await self._make_request(prompt)
        print(f'ai_response: {ai_response}')
        return ai_response
