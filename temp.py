import json
import os
from copy import deepcopy
from typing import List

import dotenv
import numpy as np
import requests
from pydantic import BaseModel, Field, create_model

dotenv.load_dotenv()

API_KEY = os.environ.get("API_KEY")
BASE_URL = os.environ.get("BASE_URL") or "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("MODEL") or "google/gemini-2.5-pro-exp-03-25:free"


class QuestionBlock(BaseModel):
    question: str = Field(
        ...,
        description="The question itself, providing context, numbers, events, etc.",
    )
    solution: str = Field(
        ...,
        description="Solution to the problem (with reasoning and calculation). Be detailed: What are the given info, what are the step by step reasonings.",
    )
    choice_true: str = Field(
        ...,
        description="A concise CORRECT answer. MUST BE CONSISTENT WITH THE SOLUTION ABOVE.",
    )
    choices_false: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="List of other choices, must be ALL WRONG",
    )


def handler():
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return LLM's response.
    """

    prompt_content = """Help me generate a multiple choice exam about SQL and database.
    """
    n_problems = 5

    schema = create_model(
        "TrueFalseQuestions",
        **{f"q{i}": (QuestionBlock, ...) for i in range(n_problems)},
    ).model_json_schema()

    print(json.dumps(schema, indent=4))

    response_raw = requests.post(
        url=BASE_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt_content,
                }
            ],
            "require_parameters": True,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "multiple_choice",
                    "strict": True,
                    "schema": schema,
                },
            },
        },
    ).json()
    assert response_raw is not None

    return json.dumps(response_raw, indent=4)

    response = json.loads(response_raw)
    for key in response.keys():
        response_curr = response[key]
        ptype = "multiple_choice"
        choices = deepcopy(response_curr["choices_false"])
        is_true = np.random.randint(4)
        choices.insert(is_true, response_curr["choice_true"])
        loc = locals()
        response_curr.update(
            {_key: loc[_key] for _key in ["choices", "is_true", "ptype"]}
        )

    return response


if __name__ == "__main__":
    print(handler())
