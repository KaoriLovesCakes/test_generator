import os

import dotenv
from google import genai

dotenv.load_dotenv()

API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL") or "gemini-2.0-flash"

client = genai.Client(api_key=API_KEY)


def handler(prompt_content: str, n_problems: int):
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return LLM's response.
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt_content,
        config={
            "temperature": 1.5,
        },
    ).text
    assert response is not None

    return ({"q0": {"raw": response}}, response)
