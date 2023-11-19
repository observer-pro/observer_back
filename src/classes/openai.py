import os
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AsyncOpenAI, BadRequestError

load_dotenv(Path(__file__).parent.parent.parent / '.env')

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=10,
    max_retries=3
)


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
    async def _make_request(prompt: str) -> dict:
        try:
            completion = await client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            response = completion.choices[0].message.content
            return {"status": True, "content": response}
        except APIConnectionError as e:
            return {"status": False, "content": "The server could not be reached. " + str(e)}
        except BadRequestError as e:
            return {"status": False, "content": "Bad request. " + str(e)}
        except APIStatusError as e:
            return {"status": False, "content": str(e.status_code) + " " + str(e)}

    async def get_explanation(self, task_text: str, user_solution_code: str) -> dict:
        prompt = self._build_prompt(task_text, user_solution_code)
        ai_response = await self._make_request(prompt)
        return ai_response
